"""commit-msg hook (.githooks/commit-msg): a commit message ends with a Co-Authored-By trailer naming the model
that made the commit, as CLAUDE.md "Commits" says.

`git config core.hooksPath .githooks` turns it on (the bootstrap skill does). Set "commit_trailer": false in
tools/leanground.json to turn the trailer rule off, and "commit_body": true to require a body as well.
Standard library only.
"""

import json
import re
import sys
from pathlib import Path

TRAILER = re.compile(r"^Co-Authored-By:\s+(.+?)\s+<([^<>\s]+@[^<>\s]+\.[^<>\s]+)>$", re.IGNORECASE)
GENERIC_TRAILER = re.compile(r"^[A-Za-z0-9-]+:\s+\S.*$")


def problems(message, require_trailer=True, require_body=False):
    """What is wrong with a commit message, as sentences; empty when it passes."""
    lines = [line.strip() for line in message.splitlines()]
    meaningful = [line for line in lines if line and not line.startswith("#")]
    if not meaningful:
        return ["the commit message is empty"]
    found = []
    ends_with_trailer = bool(TRAILER.match(meaningful[-1]))
    if require_trailer and not ends_with_trailer:
        found.append("it must end with Co-Authored-By: <model> <noreply address>, naming the model that made it")
    if require_body:
        body = [line for line in meaningful[1:] if not TRAILER.match(line) and not GENERIC_TRAILER.match(line)]
        if not body:
            found.append("it needs a body saying why, the judgments made, and how it was verified")
    return found


def main(args):
    if not args:
        print("commit-msg: git gave no message file.", file=sys.stderr)
        return 1
    repo = Path(__file__).resolve().parent.parent
    try:
        config = json.loads((repo / "tools" / "leanground.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        config = {}
    message = Path(args[0]).read_text(encoding="utf-8", errors="replace")
    found = problems(message, config.get("commit_trailer", True), config.get("commit_body", False))
    if not found:
        return 0
    print("Commit message rejected:", file=sys.stderr)
    for problem in found:
        print(f"- {problem}", file=sys.stderr)
    print('See CLAUDE.md, "Commits".', file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
