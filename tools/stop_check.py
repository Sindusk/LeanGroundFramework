"""Stop hook (.claude/settings.json): reminds the agent of tracked changes it has not committed, and of commits
it has not pushed when tools/leanground.json says leave to commit is leave to push.

Prints a systemMessage for the harness, or {} when there is nothing to remind. Standard library only; anything
unexpected prints {}.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, encoding="utf-8", errors="replace").stdout


def reminder(repo):
    """The reminder for repo's state, or None."""
    try:
        config = json.loads((Path(repo) / "tools" / "leanground.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        config = {}
    found = []
    if git(repo, "status", "--porcelain", "--untracked-files=no").strip():
        found.append("uncommitted tracked changes")
    if config.get("push_on_commit", True) and "[ahead " in git(repo, "status", "-sb").split("\n", 1)[0]:
        found.append("unpushed commits")
    if not found:
        return None
    branch = config.get("branch", "main")
    return (f"Reminder: {' and '.join(found)}. Commit at a logical checkpoint and push to {branch} as CLAUDE.md"
            " \"Commits\" says, once the build and python tools/docs.py check pass. (tools/stop_check.py)")


def main():
    try:
        event = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except ValueError:
        event = {}
    try:
        repo = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
        message = reminder(repo)
    except Exception:
        message = None
    print(json.dumps({"systemMessage": message} if message else {}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
