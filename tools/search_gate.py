"""PreToolUse hook (.claude/settings.json): one way to search and read the repository's tracked files.

Agents search five ways (the Grep tool, git grep, grep, Select-String, Get-Content) and sometimes Read a
long source file whole where `docs.py sig` and a range would do. This refuses, with the route to use:

- Get-Content, Select-String, cat or a grep that starts a command, aimed at tracked documents or source
  (docs/, tools/, .claude/, the source roots in tools/baseline.json, and *.md, *.json, *.py and the
  languages `sig` reads): use the Grep tool or `git grep`, and Read or `tools/docs.py` to read. Logs, build
  output and anything after a pipe pass.
- Read of a source file in a language `sig` reads, inside the repository and longer than long_file_lines
  (tools/baseline.json) with no limit: `docs.py sig`, then a range.

Standard library only. Exit 2 refuses (its stderr is the reason); Codex gets its structured deny instead;
anything unexpected exits 0.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import docs_sig  # noqa: E402

LONG_FILE = 400
EXTENSIONS = sorted({"md", "json", "py", *(suffix[1:] for suffix in docs_sig.ADAPTERS)})
# a search or read command at the start of a command, not fed by a pipe
SHELL_READ = re.compile(r"(^|[;&\n]|&&|\|\|)\s*(grep|rg|Get-Content|gc|cat|type|Select-String|sls)\b", re.I)
OUTPUT = re.compile(r"(^|[/\\])(build|dist|out|run|logs?|node_modules|target|coverage)[/\\]|\.log\b")
ROUTE = ("Search tracked files with the Grep tool or `git grep`; read them with Read (a range) or "
         "`python tools/docs.py` (sig, where, a section). Logs and build output may use the shell. (tools/search_gate.py)")


def settings(repo):
    path = Path(repo) / "tools" / "baseline.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def tracked_pattern(roots):
    folders = ["src", "tools", "docs", r"\.claude"] + [re.escape(root.strip("/")) for root in roots]
    return re.compile(rf"""(^|[\s'"=(])(\.?[/\\]?({'|'.join(folders)})[/\\]|[\w./\\-]+\.({'|'.join(EXTENSIONS)})\b)""")


def refusal(event, repo):
    """The reason to refuse a tool call, or None."""
    name, given = event.get("tool_name"), event.get("tool_input") or {}
    config = settings(repo)
    if name in ("Bash", "PowerShell", "Shell"):
        command = given.get("command", "")
        tracked = tracked_pattern(config.get("source_roots", []))
        for match in SHELL_READ.finditer(command):
            rest = re.split(r"[|;\n]|&&|\|\|", command[match.end():], maxsplit=1)[0]
            if tracked.search(rest) and not OUTPUT.search(rest):
                return f"{match.group(2)} on a tracked file. {ROUTE}"
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
