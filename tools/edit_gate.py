"""PreToolUse hook (.claude/settings.json): refuses shell rewrites of tracked files.

Editing a file through the shell (`sed -i`, a redirect, a heredoc, a throwaway script that rewrites it) fails
in ways the dedicated tools do not: quoting that silently changes the text, a replace that matches nothing
and exits 0, line endings flipped for the whole file, and the file echoed back into the conversation. Each
costs a round trip; Edit and Write fail loudly, in place. The rule was written in prose first and ignored,
so it is mechanical.

A path is protected when it is inside this git repository, not gitignored, and already exists: creating a
new file is not a rewrite. Reads are never blocked; only writes are refused:

1. `sed -i` on a protected path.
2. A redirect or `tee` into one (`2>&1`, `>&2` and `/dev/null` are descriptors, not files).
3. An inline script (a heredoc, `python -c`, `node -e`, PowerShell's Set-Content, Add-Content or Out-File)
   that writes and names a protected path.
4. An unreviewed script (untracked, gitignored or outside the repository) run by path that writes and names
   one. A committed script is reviewed code and runs freely.

Opting out: a project that must write from the shell creates `.claude/allow-shell-edits`; a one-off command
sets `ALLOW_SHELL_EDITS=1`. Standard library only. Exit 2 refuses (its stderr is the reason); Codex gets its
structured deny instead; anything unexpected exits 0.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

WRITE_MARKER = re.compile(
    r"\bwriteFileSync\b|\bappendFileSync\b|\bcreateWriteStream\b|\bopen\s*\([^)]*['\"][rab+]*w|\.write_text\s*\("
    r"|\bshutil\.(copy|move)\b|\bos\.replace\s*\(|\bSet-Content\b|\bAdd-Content\b|\bOut-File\b")
HEREDOC = re.compile(r"<<-?\s*[\"']?\w+")
INLINE_EVAL = re.compile(r"\b(?:node|deno|bun|python3?|py|perl|ruby)\b[^\n|;&]*\s-(?:e|c)\b")
PS_WRITE = re.compile(r"\b(?:Set-Content|Add-Content|Out-File)\b")
INVOCATION = re.compile(r"\b(?:node|deno|bun|python3?|py)\s+(?:-[\w-]+\s+)*([\"']?)([^\s\"'|&;<>()]+\.(?:mjs|cjs|js|ts|py))\1")
QUOTED = re.compile(r"(['\"])(?:\\.|(?!\1)[^\\])*\1")
MESSAGE = ("Tracked files are edited only with the harness's structured edit tool (in Claude Code: Edit for existing\n"
           "files, Write for new ones), not sed -i, a redirect, a heredoc or a throwaway script. Shell rewrites fail\n"
           "in ways that each cost a round trip: quoting errors, silent no-matches, line-ending flips, and echoing\n"
           "the whole file back into context.\n\n")
OPT_OUT = ("Read-only analysis scripts are fine; only writes are refused. If this project needs shell writes, create\n"
           ".claude/allow-shell-edits in its root, or run the one command with ALLOW_SHELL_EDITS=1. (tools/edit_gate.py)")


class Repo:
    """What git says about paths in one repository."""

    def __init__(self, cwd):
        self.cwd = Path(cwd)
        top = self.git("rev-parse", "--show-toplevel")
        self.root = Path(top.stdout.strip()).resolve() if top.returncode == 0 else None
        self.ignored = {}

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.cwd, capture_output=True, text=True)

    def absolute(self, candidate):
        path = Path(candidate)
        return (path if path.is_absolute() else self.cwd / path).resolve()

    def inside(self, path):
        try:
            return path != self.root and bool(path.relative_to(self.root).parts)
        except ValueError:
            return False

    def protected(self, candidate):
        """Inside the repository, existing, and not gitignored."""
        path = self.absolute(candidate)
        if not self.inside(path) or not path.exists():
            return False
        if path not in self.ignored:
            self.ignored[path] = self.git("check-ignore", "-q", "--", str(path)).returncode == 0
        return not self.ignored[path]

    def tracked(self, candidate):
        path = self.absolute(candidate)
        return self.inside(path) and self.git("ls-files", "--error-unmatch", "--", str(path)).returncode == 0


def expand_assignments(text):
    """The command with $NAME and ${NAME} replaced by values the same command assigns, so a path written through a
    variable is judged as itself."""
    values = {}
    for match in re.finditer(r"(?:^|[\s;&|(])([A-Za-z_]\w*)=(\"[^\"\n]*\"|'[^'\n]*'|[^\s;&|()]+)", text):
        values[match.group(1)] = re.sub(r"^([\"'])([\s\S]*)\1$", r"\2", match.group(2))
    if not values:
        return text
    return re.sub(r"\$(?:\{([A-Za-z_]\w*)\}|([A-Za-z_]\w*))",
                  lambda m: values.get(m.group(1) or m.group(2), m.group(0)), text)


def looks_like_path(repo, token):
    """A filesystem path rather than a flag, a URL, a command line or prose."""
    if not token or len(token) > 300 or re.search(r"\s", token) or re.match(r"[-+&]", token):
        return False
    if re.match(r"[a-z][a-z0-9+.-]*://", token, re.I):
        return False
    separated = bool(re.search(r"[/\\]", token))
    if not separated and not re.search(r"\.[A-Za-z0-9]{1,10}$", token):
        return False
    path = repo.absolute(token)
    # A bare dotted token (JSON.stringify) must exist to count; a path with a separator needs its folder.
    return path.exists() if not separated else path.exists() or path.parent.exists()


def path_tokens(repo, text):
    tokens = [m.group(2) for m in re.finditer(r"(['\"])([^'\"\n]{1,300})\1", text)]
    tokens += [m.group(1) for m in re.finditer(r"(?:^|[\s=(,;|&])([\w.~][\w./\\-]{0,299})", text)]
    return [token for token in tokens if looks_like_path(repo, token)]


def redirect_targets(text):
    targets = [m.group(2) for m in re.finditer(r"(?:^|[\s;|&(])\d?>>?\s*(?!&)([\"']?)([^\s\"'|&;<>()]+)\1", text)]
    targets += [m.group(2) for m in re.finditer(r"\btee\s+(?:-a\s+)?([\"']?)([^\s\"'|&;<>()]+)\1", text)]
    return targets


def refusal(event, cwd):
    """(what, paths) for a command that would rewrite a protected file, or None."""
    if event.get("tool_name") not in ("Bash", "PowerShell", "Shell"):
        return None
    command = expand_assignments(str((event.get("tool_input") or {}).get("command", "")))
    if not command.strip() or re.search(r"\bALLOW_SHELL_EDITS\s*=\s*1\b", command):
        return None
    repo = Repo(cwd)
    if repo.root is None or (repo.root / ".claude" / "allow-shell-edits").exists():
        return None

    # Heredoc bodies are data (a commit message may discuss sed -i), so the syntax checks skip them.
    syntax = re.sub(r"<<-?\s*([\"']?)(\w+)\1[\s\S]*?^\s*\2\s*$", lambda m: m.group(0).split("\n", 1)[0],
                    command, flags=re.MULTILINE)
    blanked = QUOTED.sub(lambda m: " " * len(m.group(0)), syntax)

    offenders = []
    for match in re.finditer(r"\bsed\b[^|;&\n]*", blanked):
        if re.search(r"\s-[a-zA-Z]*i\b", match.group(0)):
            span = syntax[match.start():match.end()]
            offenders += [token for token in path_tokens(repo, span) if repo.protected(token)]
    if offenders:
        return "`sed -i` against a tracked file", offenders

    offenders = [target for target in redirect_targets(syntax) if repo.protected(target)]
    if offenders:
        return "a shell redirect that would overwrite a tracked file", offenders

    inline = HEREDOC.search(command) or INLINE_EVAL.search(blanked) or PS_WRITE.search(blanked)
    if inline and WRITE_MARKER.search(command):
        offenders = [token for token in path_tokens(repo, command) if repo.protected(token)]
        if offenders:
            return "a script that rewrites a tracked file", offenders

    for match in INVOCATION.finditer(command):
        script = repo.absolute(match.group(2))
        if not script.is_file() or repo.tracked(script):
            continue
        try:
            body = script.read_text(encoding="utf-8")
        except OSError:
            continue
        if WRITE_MARKER.search(body):
            offenders = [token for token in path_tokens(repo, body) if repo.protected(token)]
            if offenders:
                return f"an unreviewed script ({match.group(2)}) that rewrites tracked files", offenders
    return None


def deny(event, what, paths):
    listed = "\n".join(f"  - {path}" for path in list(dict.fromkeys(paths))[:5])
    reason = f"Blocked: {what}.\n\n{MESSAGE}Paths this command would write:\n{listed}\n\n" \
             "Read the file, then patch the part that changes; do not regenerate it.\n\n" + OPT_OUT
    if isinstance(event.get("turn_id"), str) and isinstance(event.get("tool_use_id"), str):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
        return 0
    print(reason, file=sys.stderr)
    return 2


def main():
    try:
        event = json.load(sys.stdin)
        if os.environ.get("ALLOW_SHELL_EDITS") == "1":
            return 0
        tool_input = event.get("tool_input") or {}
        cwd = event.get("cwd") or tool_input.get("working_directory") or tool_input.get("cwd") or os.getcwd()
        found = refusal(event, cwd)
    except Exception:
        return 0
    return deny(event, *found) if found else 0


if __name__ == "__main__":
    sys.exit(main())
