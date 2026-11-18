"""pre-commit hook (.githooks/pre-commit): a commit that stages a file `docs.py check` guards runs the check first,
and is refused with the check's output when it fails, so a budget overrun or a broken citation never reaches the
branch because a skill edit was committed without it.

Guarded: a file with a budget in tools/leanground.json, CLAUDE.md, AGENTS.md, anything under .claude/, LEDGER.md
and DESIGN.md. Any other commit is untouched and costs one `git diff --cached`. The check reads the working tree,
as every docs.py command does, so stage what it should judge. Works bootstrapped or not: check itself knows the
difference. `git config core.hooksPath .githooks` turns it on (the lg-bootstrap skill does); `git commit
--no-verify` skips it. Standard library only.
"""

import json
import subprocess
import sys
from pathlib import Path

GUARDED = ("CLAUDE.md", "AGENTS.md", "LEDGER.md", "DESIGN.md")
GUARDED_FOLDER = ".claude/"


def guarded(staged, budgets):
    """The staged names (relative to the repository, / separated) that docs.py check guards."""
    return [name for name in staged if name in GUARDED or name in budgets or name.startswith(GUARDED_FOLDER)]


def staged_names(repo):
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"], cwd=repo, capture_output=True,
                         encoding="utf-8", errors="replace")
    return [name for name in out.stdout.split("\0") if name] if out.returncode == 0 else None


def main(repo):
    repo = Path(repo)
    try:
        budgets = json.loads((repo / "tools" / "leanground.json").read_text(encoding="utf-8")).get("budgets", {})
    except (OSError, ValueError):
        budgets = {}
    staged = staged_names(repo)
    if staged is None:
        print("pre-commit: git could not list the staged files; the commit was not checked.", file=sys.stderr)
        return 0
    found = guarded(staged, budgets)
    if not found:
        return 0
    check = subprocess.run([sys.executable, str(repo / "tools" / "docs.py"), "check"], cwd=repo, capture_output=True,
                           encoding="utf-8", errors="replace")
    if check.returncode == 0:
        return 0
    print(f"Commit refused: it stages {found[0]}{f' and {len(found) - 1} more' if len(found) > 1 else ''}, which"
          " python tools/docs.py check guards, and the check fails:", file=sys.stderr)
    print(file=sys.stderr)
    print((check.stdout + check.stderr).rstrip(), file=sys.stderr)
    print(file=sys.stderr)
    print("Fix what it reports, stage the fix and commit again.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent))
