"""The package gate: runs the project's verify steps in order, each command's output to its own log, and writes a
short summary the agent reads in place of any log.

    python tools/verify.py              run every step
    python tools/verify.py --resume     rerun the failed step and every step after it
    python tools/verify.py --only <name>  run one step
    python tools/verify.py --list       print the steps

The steps are tools/leanground.json "verify_steps", in order, each {"name": ..., "command": ...} with an optional
"max_minutes"; "verify_max_minutes" holds the whole run to a budget (0 or absent: no limit). A command is a string,
run by the platform's shell from the repository root (cmd on Windows, sh elsewhere), or a list, run as it stands.
An empty list is refused: the project has not set its steps.

Nothing a step prints reaches the console: each step's output goes to working/verify/<n>-<name>.log and the console
gets one line per step (name, PASS or FAIL, seconds). The run stops at the first failure and names the steps it did
not run, since a stopped run is incomplete, never green. A step past its own limit, or past what is left of the
run's budget, is stopped and fails, and the summary says which limit it passed.

working/verify/summary.md holds each step's result and time, the total, the slowest steps, and the failing step's
log path with its last lines. It is overwritten at the start of every run, a refused one included, so an earlier
run's pass is never read as this run's [PF-582]. working/verify/state.json keeps the run for --resume, which carries
the earlier passes into the summary and refuses when the step list has changed since, since the carried passes
would then not be this list's. --only leaves that state as it was. The last line printed names the summary and the
result, so a backgrounded run's notice is enough.

Exit codes: 0 every step ran and passed (with --only, that step); 1 a step failed, passed a limit or was
interrupted; 2 refused before the first step (no steps, a bad step, a bad flag, nothing to resume).
Standard library only.
"""

import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

OUT = Path("working") / "verify"
TAIL_LINES = 30
TAIL_WIDTH = 300
SLOWEST = 3
USAGE = "Usage: python tools/verify.py [--resume | --only <name> | --list]"


class Refused(Exception):
    pass


def load_steps(repo):
    """The step list and the run's budget in minutes, or Refused naming what is wrong with them."""
    try:
        config = json.loads((repo / "tools" / "leanground.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Refused(f"tools/leanground.json could not be read ({error}).")
    steps = config.get("verify_steps", [])
    budget = config.get("verify_max_minutes", 0) or 0
    if not isinstance(steps, list) or not steps:
        raise Refused('The project has not set its verify steps: tools/leanground.json "verify_steps" is empty.'
                      ' Each step is {"name": ..., "command": ...}; see LEANGROUND.md, "Settings".')
    if not isinstance(budget, (int, float)) or budget < 0:
        raise Refused('"verify_max_minutes" must be a number of minutes, 0 for no limit.')
    seen = set()
    for number, step in enumerate(steps, 1):
        if not isinstance(step, dict) or not isinstance(step.get("name"), str) or not step["name"].strip():
            raise Refused(f"verify step {number} has no name.")
        command = step.get("command")
        if not (isinstance(command, str) and command.strip()) and not (
                isinstance(command, list) and command and all(isinstance(part, str) for part in command)):
            raise Refused(f'verify step "{step["name"]}" has no command.')
        limit = step.get("max_minutes", 0) or 0
        if not isinstance(limit, (int, float)) or limit < 0:
            raise Refused(f'verify step "{step["name"]}": "max_minutes" must be a number of minutes.')
        if step["name"] in seen:
            raise Refused(f'two verify steps are named "{step["name"]}".')
        seen.add(step["name"])
    return steps, budget


def log_name(number, name):
    return f"{number}-{re.sub(r'[^A-Za-z0-9_.-]+', '-', name).strip('-') or 'step'}.log"


def kill_tree(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
    process.wait()


def run_step(repo, step, log, seconds_allowed):
    """Runs one step with its output to log: (exit code, or None when stopped at seconds_allowed, seconds taken)."""
    command = step["command"]
    started = time.monotonic()
    with open(log, "wb") as out:
        process = subprocess.Popen(command, shell=isinstance(command, str), cwd=repo, stdin=subprocess.DEVNULL,
                                   stdout=out, stderr=subprocess.STDOUT, start_new_session=os.name != "nt")
        try:
            code = process.wait(timeout=seconds_allowed)
        except subprocess.TimeoutExpired:
            kill_tree(process)
            code = None
        except BaseException:
            kill_tree(process)
            raise
    return code, time.monotonic() - started


def tail(log):
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ["(the log could not be read)"]
    return [line if len(line) <= TAIL_WIDTH else line[:TAIL_WIDTH] + " ..." for line in lines[-TAIL_LINES:]]


def summary_text(title, started, results, budget, note=""):
    """The summary file's text. results: dicts with name, status (pass, FAIL, not run), seconds, log, reason."""
    lines = [f"# verify: {title}", "", f"Run {started:%Y-%m-%d %H:%M:%S}."]
    if note:
        lines.append(note)
    if results:
        timed = [entry for entry in results if entry.get("seconds") is not None]
        total = sum(entry["seconds"] for entry in timed if not entry.get("carried"))
        lines += [f"Total {total:.1f} s{f' against a budget of {budget:g} min' if budget else ''}"
                  f"{', earlier passes not counted' if any(entry.get('carried') for entry in timed) else ''}.", "",
                  "| Step | Result | Seconds | Log |", "|---|---|---|---|"]
        for entry in results:
            seconds = "" if entry.get("seconds") is None else f"{entry['seconds']:.1f}"
            result = entry["status"] + (f" ({entry['reason']})" if entry.get("reason") else "")
            lines.append(f"| {entry['name']} | {result} | {seconds} | {entry.get('log') or ''} |")
        slowest = sorted((entry for entry in timed if not entry.get("carried")), key=lambda entry: -entry["seconds"])
        if slowest:
            lines += ["", "Slowest: " + ", ".join(f"{entry['name']} {entry['seconds']:.1f} s"
                                                  for entry in slowest[:SLOWEST]) + "."]
        failed = [entry for entry in results if entry["status"] == "FAIL"]
        if failed:
            log = failed[0]["log"]
            lines += ["", f"## {failed[0]['name']}: the last lines of {log}", "", "```", *tail(Path(failed[0]["path"])),
                      "```"]
    return "\n".join(lines) + "\n"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def refuse(repo, started, reason):
    write(repo / OUT / "summary.md", summary_text("REFUSED before its first step", started, [], 0, reason))
    print(reason)
    print(f"verify: REFUSED, nothing ran. Summary: {(OUT / 'summary.md').as_posix()}")
    return 2


def parse(argv):
    mode, only = "run", None
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg in ("--resume", "--list") and mode == "run":
            mode = arg[2:]
        elif arg == "--only" and mode == "run" and args:
            mode, only = "only", args.pop(0)
        elif arg.startswith("--only=") and mode == "run" and len(arg) > 7:
            mode, only = "only", arg[7:]
        else:
            raise Refused(f"{arg!r} is not understood here. {USAGE}")
    return mode, only


def main(argv, repo):
    repo = Path(repo)
    started = datetime.now()
    try:
        mode, only = parse(argv)
    except Refused as refusal:
        return refuse(repo, started, str(refusal))
    try:
        steps, budget = load_steps(repo)
    except Refused as refusal:
        if mode == "list":
            print(refusal)
            return 2
        return refuse(repo, started, str(refusal))
    if mode == "list":
        for number, step in enumerate(steps, 1):
            command = step["command"] if isinstance(step["command"], str) else subprocess.list2cmdline(step["command"])
            limit = f" (at most {step['max_minutes']:g} min)" if step.get("max_minutes") else ""
            print(f"{number}. {step['name']}: {command}{limit}")
        print(f"Run budget: {f'{budget:g} min' if budget else 'none'}.")
        return 0

    state_path = repo / OUT / "state.json"
    results = [{"name": step["name"], "status": "not run", "seconds": None, "log": None, "path": None}
               for step in steps]
    first, last = 0, len(steps)
    note = ""
    if mode == "resume":
        try:
            saved = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return refuse(repo, started, "There is no earlier run to resume; run python tools/verify.py.")
        if saved.get("steps") != steps:
            return refuse(repo, started, "The verify steps have changed since the run being resumed, so its passes"
                                         " are not this list's; run python tools/verify.py whole.")
        first = next((n for n, entry in enumerate(saved["results"]) if entry["status"] != "pass"), None)
        if first is None:
            return refuse(repo, started, "The earlier run passed every step; there is nothing to resume.")
        for n in range(first):
            results[n] = dict(saved["results"][n], status="pass", carried=True, reason="earlier run")
        note = f"Resumed at {steps[first]['name']}; the steps before it passed in the run of {saved['started']}."
    elif mode == "only":
        found = [n for n, step in enumerate(steps) if step["name"] == only]
        if not found:
            return refuse(repo, started, f"No verify step is named {only!r}; python tools/verify.py --list.")
        first, last = found[0], found[0] + 1
        results = [results[first]]
        note = f"Only the step {only} ran: this is not the whole gate."

    def save():
        if mode != "only":
            write(state_path, json.dumps({"started": f"{started:%Y-%m-%d %H:%M:%S}", "steps": steps,
                                          "results": results}, indent=2))

    out = repo / OUT
    # Written before the first step, so a run killed midway leaves no earlier run's result behind.
    write(out / "summary.md", f"# verify: RUNNING\n\nRun {started:%Y-%m-%d %H:%M:%S}, not finished.\n")
    if mode == "run":
        for old in out.glob("*.log"):
            old.unlink()
    run_started = time.monotonic()
    failed = None
    for n in range(first, last):
        step = steps[n]
        entry = results[0] if mode == "only" else results[n]
        log = OUT / log_name(n + 1, step["name"])
        entry.update(log=log.as_posix(), path=str(repo / log))
        allowed, limit_reason = None, ""
        if step.get("max_minutes"):
            allowed, limit_reason = step["max_minutes"] * 60, f"passed its limit of {step['max_minutes']:g} min"
        if budget:
            left = budget * 60 - (time.monotonic() - run_started)
            if allowed is None or left < allowed:
                allowed, limit_reason = max(left, 0), f"passed the run's budget of {budget:g} min"
        print(f"{step['name']} ...", end="", flush=True)
        try:
            code, seconds = run_step(repo, step, repo / log, allowed)
        except KeyboardInterrupt:
            entry.update(status="FAIL", reason="interrupted")
            failed = entry
            print(" FAIL (interrupted)", flush=True)
            break
        except OSError as error:
            code, seconds, limit_reason = "", 0.0, f"could not start: {error}"
        entry["seconds"] = seconds
        if code == 0:
            entry["status"] = "pass"
            print(f" PASS {seconds:.1f}s", flush=True)
        else:
            reason = f"exit {code}" if isinstance(code, int) else limit_reason
            entry.update(status="FAIL", reason=reason)
            print(f" FAIL {seconds:.1f}s ({reason})", flush=True)
            failed = entry
        save()
        if failed:
            break
    save()

    unrun = [entry["name"] for entry in results if entry["status"] == "not run"]
    if failed:
        title = f"FAILED at {failed['name']} ({failed['reason']})"
        if unrun:
            title += f"; not run: {', '.join(unrun)}"
    elif mode == "only":
        title = f"PASSED the one step {only}"
    else:
        title = f"PASSED, all {len(steps)} steps"
    write(out / "summary.md", summary_text(title, started, results, budget, note))
    print(f"verify: {title}. Summary: {(OUT / 'summary.md').as_posix()}")
    return 1 if failed else 0


if __name__ == "__main__":
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, encoding="utf-8")
    sys.exit(main(sys.argv[1:], top.stdout.strip() if top.returncode == 0 else Path(__file__).resolve().parent.parent))
