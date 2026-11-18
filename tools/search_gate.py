"""PreToolUse hook (.claude/settings.json): one way to search and read the repository's tracked files.

Agents search five ways (the Grep tool, git grep, grep, Select-String, Get-Content) and sometimes Read a
long source file whole where `docs.py sig` and a range would do. This refuses, with the route to use:

- Get-Content, Select-String, cat or a grep that starts a command, aimed at tracked documents or source
  (docs/, tools/, .claude/, the source roots in tools/leanground.json, and *.md, *.json, *.py and the
  languages `sig` reads): use the Grep tool or `git grep`, and Read or `tools/docs.py` to read. Logs, build
  output and anything after a pipe pass, as do the small data files `shell_read_paths` (tools/leanground.json)
  names by glob, which agents read beside a command. A path is refused only when git tracks it, resolved from
  a leading `cd` when that folder exists: untracked and gitignored files and files outside the repository pass.
  A quoted path is one word, spaces and punctuation included.
- A guessed line window over shell_window_lines (tools/leanground.json, 60 by default) of a tracked document
  or source: `sed -n 'A,Bp'`, `head -n N`, `tail -n N` (or `+N`) and `awk 'NR>=A && NR<=B'` at the start of a
  command: use `docs.py sig <Name>` (or Name:member), a section or heading, or Read with offset and limit. A
  smaller window passes, and logs, build output, pipes and `shell_read_paths` pass as above.
- A search of the whole disk (`find /`, `find /c`, `find ~`, a recursive listing of a drive or the home folder):
  on Windows the tool's timeout ends the shell but not the search, which runs on unseen for hours. Search a
  named folder instead.
- Read of a source file in a language `sig` reads, inside the repository and longer than long_file_lines
  (tools/leanground.json) with no limit: `docs.py sig`, then a range.

Standard library only. Exit 2 refuses (its stderr is the reason); Codex gets its structured deny instead;
anything unexpected exits 0.
"""

import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import docs_sig  # noqa: E402

LONG_FILE = 400
WINDOW_LINES = 60
EXTENSIONS = sorted({"md", "json", "py", *(suffix[1:] for suffix in docs_sig.ADAPTERS)})
# a search or read command at the start of a command, not fed by a pipe
SHELL_READ = re.compile(r"(^|[;&\n]|&&|\|\|)\s*(grep|rg|Get-Content|gc|cat|type|Select-String|sls)\b", re.I)
# a reader of a line window, at the start of a command the same way
WINDOW_READ = re.compile(r"(^|[;&\n]|&&|\|\|)\s*(sed|head|tail|awk)\b")
# one sed print command: 10,80p, 10,+70p, 10,$p, 5p
SED_PRINT = re.compile(r"\s*(\d+|\$)\s*(?:,\s*(\+?\d+|\$))?\s*p\s*")
# one awk comparison of the line number: NR>=10, NR < 80, NR==5
AWK_NR = re.compile(r"\bNR\s*(>=|<=|==|>|<)\s*(\d+)")
OUTPUT = re.compile(r"(^|[/\\])(build|dist|out|run|logs?|node_modules|target|coverage)[/\\]|\.log\b")
QUOTED = re.compile(r""""[^"\n]*"|'[^'\n]*'""")
# a shell word: quoted parts and bare characters run together, so "two words.md" is one word
WORD = re.compile(r"""(?:"[^"\n]*"|'[^'\n]*'|[^\s'"])+""")
# the folders a command's leading `cd`s move to
LEADING_CD = re.compile(r"""\s*(?:cd|Set-Location|sl)\s+(?:/d\s+)?(?:"([^"]+)"|'([^']+)'|([^\s;&|]+))\s*(?:;|&&|\n)""", re.I)
# a drive, the filesystem root or the home folder, as one word
DISK_ROOT = re.compile(r"(/|/[a-z]/?|/[a-z]/Users/?|[a-z]:[/\\]?|[a-z]:[/\\]Users[/\\]?|(~|\$HOME|\$\{HOME\}|\$env:USERPROFILE)[/\\]?)",
                       re.I)
# Get-ChildItem's -Recurse or -r, ls's -R alone or in a bundle (-lR), dir's /s
RECURSIVE = re.compile(r"(?i:-Recurse\b.*|-r|/s)|-[a-zA-Z]*R[a-zA-Z]*")
ROUTE = ("Search tracked files with the Grep tool or `git grep`; read them with Read (a range) or "
         "`python tools/docs.py` (sig, where, a section). Logs and build output may use the shell. (tools/search_gate.py)")
DISK_ROUTE = ("A search of the whole disk (find /, find ~, a recursive listing of a drive) can outlive the tool's "
              "timeout: on Windows the timeout ends the shell but not the search, which runs on unseen. Search a "
              "named folder instead. (tools/search_gate.py)")


def window_route(program, shown, name, limit):
    return (f"{program} prints {shown} lines of {name}, a guessed window over {limit} (shell_window_lines). Read by "
            "name instead: `python tools/docs.py sig <Name>` (or Name:member) for code, `python tools/docs.py "
            "<section>` or a heading for a document, or Read with offset and limit. A window of "
            f"{limit} lines or fewer passes. (tools/search_gate.py)")


def settings(repo):
    path = Path(repo) / "tools" / "leanground.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def tracked_pattern(roots):
    folders = ["src", "tools", "docs", r"\.claude"] + [re.escape(root.strip("/")) for root in roots]
    return re.compile(rf"""(^|[\s'"=(])(\.?[/\\]?({'|'.join(folders)})[/\\]|[^\s'"=()]+\.({'|'.join(EXTENSIONS)})\b)""")


def words(text):
    """The shell words of text, each without its quotes: 'cat "two words.md" -n' is ['cat', 'two words.md', '-n']."""
    return [re.sub(r""""([^"]*)"|'([^']*)'""", lambda m: m.group(1) if m.group(1) is not None else m.group(2),
                   match.group(0)) for match in WORD.finditer(text)]


def as_path(word, base):
    """A shell word as an absolute path: Git Bash's /c/..., ~ and relative paths resolved; for an option word
    --opt=value, the value. An = in any other word is part of its path."""
    text = (word.split("=", 1)[1] if word.startswith("-") and "=" in word else word).replace("\\", "/")
    drive = re.match(r"^/([a-zA-Z])(/|$)", text)
    if drive:
        text = f"{drive.group(1)}:/{text[3:]}"
    text = os.path.expanduser(text)
    return os.path.normpath(text if os.path.isabs(text) else os.path.join(base, text))


def start_folder(command, base):
    """Where the command's reads run: its leading `cd`s followed while their folders exist."""
    at = 0
    while True:
        match = LEADING_CD.match(command, at)
        if not match:
            return base
        folder = as_path(next(group for group in match.groups() if group), base)
        if os.path.isdir(folder):
            base = folder
        at = match.end()


def relative(path, repo):
    """path relative to repo with / separators, or None outside it."""
    try:
        inside = os.path.relpath(path, repo)
    except ValueError:  # another drive
        return None
    return None if inside == ".." or inside.startswith(".." + os.sep) else inside.replace(os.sep, "/")


def tracked_by_git(path, repo):
    """Whether git tracks `path` (a file, a folder holding tracked files, or a glob) in `repo`. When git cannot
    say, it counts as tracked."""
    inside = relative(path, repo)
    if inside is None:
        return False
    try:
        found = subprocess.run(["git", "ls-files", "--", inside], cwd=repo, capture_output=True, encoding="utf-8",
                               errors="replace", timeout=5)
    except (OSError, subprocess.SubprocessError):
        return True
    return found.returncode != 0 or bool(found.stdout.strip())


def free_to_read(path, repo, globs):
    """Whether a glob in shell_read_paths (relative to the repository) names path."""
    inside = relative(path, repo)
    return inside is not None and any(fnmatch.fnmatch(inside, pattern) for pattern in globs)


def line_count(value, sign_means):
    """head's or tail's count ('80', '+80', '-5') as (kind, number): sign_means names what a leading sign does."""
    match = re.fullmatch(r"([+-]?)(\d+)", value)
    if not match:
        return None
    return (sign_means if match.group(1) and match.group(1) in sign_means else "first"), int(match.group(2))


def head_or_tail(program, args):
    """(file words, lines shown as a function of a file's length) for head or tail; None for bytes or a follow."""
    count, files, n = ("first", 10), [], 0
    while n < len(args):
        arg, value = args[n], None
        if arg in ("-n", "--lines") and n + 1 < len(args):
            value, n = args[n + 1], n + 1
        elif arg.startswith("--lines="):
            value = arg.split("=", 1)[1]
        elif re.fullmatch(r"-n[+-]?\d+|-\d+", arg):
            value = arg[2:] if arg.startswith("-n") else arg[1:]
        elif re.match(r"-[a-zA-Z]*[cfF]|--(bytes|follow)", arg):
            return None
        elif not arg.startswith("-") or arg == "-":
            files.append(arg)
        n += 1
        if value is not None:
            count = line_count(value, "-" if program == "head" else "+")
            if count is None:
                return None
    kind, number = count
    if kind == "-":  # head -n -5: all but the last five
        return files, lambda total: max(0, total - number)
    if kind == "+":  # tail -n +5: from line five on
        return files, lambda total: max(0, total - number + 1)
    return files, lambda total: min(number, total)


def sed_window(args):
    """(file words, lines shown) for sed -n with line-number print commands only ('10,80p', '5p;90,$p')."""
    quiet, scripts, files, n = False, [], [], 0
    while n < len(args):
        arg = args[n]
        if arg in ("--quiet", "--silent"):
            quiet = True
        elif arg.startswith("--expression="):
            scripts.append(arg.split("=", 1)[1])
        elif re.fullmatch(r"-[a-zA-Z]+", arg):
            if set(arg[1:]) & {"i", "f"}:  # an in-place edit or a script file: not a window read
                return None
            quiet = quiet or "n" in arg
            if arg.endswith("e") and n + 1 < len(args):
                scripts.append(args[n + 1])
                n += 1
        elif arg.startswith("-"):
            pass
        elif not scripts:
            scripts.append(arg)
        else:
            files.append(arg)
        n += 1
    ranges = []
    for part in re.split(r"[;\n]", ";".join(scripts)):
        if not part.strip() or re.fullmatch(r"\s*\d*\s*q\s*", part):
            continue
        match = SED_PRINT.fullmatch(part)
        if not match:
            return None
        ranges.append(match.groups())
    if not quiet or not ranges:
        return None

    def shown(total):
        lines = 0
        for first, last in ranges:
            start = total if first == "$" else int(first)
            end = start if last is None else total if last == "$" else start + int(last[1:]) if last[0] == "+" \
                else int(last)
            lines += 1 if end < start else max(0, min(end, total) - start + 1)
        return lines
    return files, shown


def awk_window(args):
    """(file words, lines shown) for an awk program that selects lines by NR ('NR>=10 && NR<=80')."""
    program, files, n = None, [], 0
    while n < len(args):
        arg = args[n]
        if arg == "-f":
            return None
        if arg in ("-F", "-v"):
            n += 1
        elif arg.startswith("-") or (program is not None and re.fullmatch(r"\w+=.*", arg)):
            pass
        elif program is None:
            program = arg
        else:
            files.append(arg)
        n += 1
    found = AWK_NR.findall(program or "")
    if not found:
        return None
    lows = [int(v) + (op == ">") for op, v in found if op in (">=", ">")]
    highs = [int(v) - (op == "<") for op, v in found if op in ("<=", "<")]
    equal = [int(v) for op, v in found if op == "=="]
    if equal:  # NR==5 one line; NR==10,NR==80 a range
        lows.append(min(equal))
        highs.append(max(equal))
    return files, lambda total: max(0, min(highs + [total]) - (max(lows) if lows else 1) + 1)


def window_reader(program, args):
    """(file words, lines shown as a function of a file's length) for a line-window read, else None."""
    if program in ("head", "tail"):
        return head_or_tail(program, args)
    return sed_window(args) if program == "sed" else awk_window(args)


def whole_disk_search(command):
    """Whether a command runs find from, or lists recursively, a drive, the filesystem root or the home folder."""
    for segment in re.split(r"[;&|\n()]", command):
        found = words(segment)
        if not found:
            continue
        program, args = found[0].lower(), found[1:]
        # dir's flags are /x, which would read as Git Bash's drive /x
        roots = [arg for arg in args if DISK_ROOT.fullmatch(arg) and not (program == "dir" and arg.startswith("/"))]
        if re.fullmatch(r"find(\.exe)?", program):
            for arg in args:  # the starting points come before the first expression
                if arg in ("-H", "-L", "-P") or arg.startswith("-O"):
                    continue
                if arg.startswith(("-", "!", "(")):
                    break
                if arg in roots:
                    return True
        elif program in ("get-childitem", "gci", "dir", "ls") and roots and any(RECURSIVE.fullmatch(a) for a in args):
            return True
    return False


def refusal(event, repo):
    """The reason to refuse a tool call, or None."""
    name, given = event.get("tool_name"), event.get("tool_input") or {}
    config = settings(repo)
    if name in ("Bash", "PowerShell", "Shell"):
        command = given.get("command", "")
        if whole_disk_search(command):
            return DISK_ROUTE
        tracked = tracked_pattern(config.get("source_roots", []))
        base = start_folder(command, event.get("cwd") or str(repo))
        free = config.get("shell_read_paths", [])
        # Quoted text is blanked to find where a read starts and stops, so a quoted ; or | is part of its path.
        blanked = QUOTED.sub(lambda m: " " * len(m.group(0)), command)
        for match in SHELL_READ.finditer(blanked):
            end = re.search(r"[|;\n]|&&|\|\|", blanked[match.end():])
            rest = command[match.end():match.end() + end.start() if end else len(command)]
            for word in words(rest):
                if OUTPUT.search(word) or not tracked.search(" " + word):
                    continue
                path = as_path(word, base)
                if not free_to_read(path, repo, free) and tracked_by_git(path, str(repo)):
                    return f"{match.group(2)} on a tracked file. {ROUTE}"
        limit = config.get("shell_window_lines", WINDOW_LINES)
        for match in WINDOW_READ.finditer(blanked):
            end = re.search(r"[|;\n]|&&|\|\|", blanked[match.end():])
            rest = command[match.end():match.end() + end.start() if end else len(command)]
            window = window_reader(match.group(2), words(rest))
            if window is None:
                continue
            for word in window[0]:
                if OUTPUT.search(word) or not tracked.search(" " + word):
                    continue
                path = as_path(word, base)
                if not os.path.isfile(path) or free_to_read(path, repo, free) or not tracked_by_git(path, str(repo)):
                    continue
                with open(path, encoding="utf-8", errors="replace") as source:
                    shown = window[1](sum(1 for _ in source))
                if shown > limit:
                    return window_route(match.group(2), shown, relative(path, str(repo)) or word, limit)
        return None
    if name == "Read" and not given.get("limit"):
        path = Path(given.get("file_path", ""))
        if path.suffix not in docs_sig.ADAPTERS or not path.is_file():
            return None
        try:
            path.resolve().relative_to(Path(repo).resolve())
        except ValueError:
            return None
        if OUTPUT.search(path.as_posix()):
            return None
        limit = config.get("long_file_lines", LONG_FILE)
        with open(path, encoding="utf-8", errors="replace") as source:
            lines = sum(1 for _ in source)
        if lines > limit:
            return (f"{path.name} is {lines} lines. `python tools/docs.py sig {path.stem}` first, then Read the "
                    f"ranges you need with offset and limit (a limit of {lines} if the whole file is truly needed).")
    return None


def deny(event, reason):
    """Refuses in the protocol the harness reads: Codex's structured decision, else stderr and exit 2."""
    if isinstance(event.get("turn_id"), str) and isinstance(event.get("tool_use_id"), str):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
        return 0
    print(reason, file=sys.stderr)
    return 2


def main():
    try:
        event = json.load(sys.stdin)
        repo = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
        reason = refusal(event, repo)
    except Exception:
        return 0
    return deny(event, reason) if reason else 0


if __name__ == "__main__":
    sys.exit(main())
