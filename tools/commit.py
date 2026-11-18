"""Commits exactly the named paths, as they are in the working tree, through a temporary index, so nothing another
session staged or left modified in this checkout reaches the commit, and nothing of theirs is lost to it.

    python tools/commit.py -F <message file> [--push] -- <path> ...
    python tools/commit.py -m <subject> [-m <paragraph>] ... [--push] -- <path> ...

Several sessions share one checkout and one index: a plain `git add` and `git commit` took another session's staged
files to the branch [MM-115], or lost a staged batch to another session's commit [MM-137]. This tool reads HEAD into
a temporary index (GIT_INDEX_FILE), puts the named paths into it as the working tree holds them (a new file needs no
`git add`; a path that is gone is committed as deleted; a folder takes every change under it), commits that, then
sets the real index's entries for exactly those paths to the new HEAD, so `git status` is clean for them. Nothing
else in the real index or the working tree changes. Repeated -m options become paragraphs, as with git, so a
one-line subject can still carry the trailer: -m "<subject>" -m "Co-Authored-By: ...".

It refuses, changing nothing: a path with no change against HEAD; a path outside the repository or gitignored; a path
someone has staged with content different from the working tree (another session's stage, which this commit would
take or undo); an empty message, or one the commit-msg rule rejects (tools/commit_msg.py); and a commit that
tools/pre_commit.py refuses (it runs on the temporary index, so it judges only what this commit stages). The commit
is made with `git commit-tree` and moves the branch only if HEAD is still the commit it was built on, so a commit
another session makes meanwhile is never undone. Those two checks are the kit's commit-msg and pre-commit hooks,
run here directly whether or not the hooks are turned on; no other hook runs.

--push pushes after the commit when "push_on_commit" is true in tools/leanground.json; without it nothing is pushed.

Hunks are out of scope: a named file is committed whole. A file that also holds another session's hunks is
committed by that session, or split by hand.

Prints one line: the short hash, the subject and the files committed. Exit codes: 0 committed (and pushed when
asked); 1 refused, nothing changed; 2 committed, but syncing the real index or the push failed (it says which).
Standard library only.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit_msg  # noqa: E402

USAGE = "Usage: python tools/commit.py (-F <message file> | -m <subject> ...) [--push] -- <path> ..."
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class Refused(Exception):
    pass


def git(repo, *args, env=None, input=None):
    """Runs git in repo with literal pathspecs; returns the completed process."""
    full = dict(os.environ if env is None else env, GIT_LITERAL_PATHSPECS="1")
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, encoding="utf-8", errors="replace",
                          env=full, input=input)


def names(process):
    return [name for name in process.stdout.split("\0") if name]


def parse(argv):
    message_file, paragraphs, push = None, [], False
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--":
            return message_file, paragraphs, push, args
        if arg == "-F" and args and message_file is None:
            message_file = args.pop(0)
        elif arg == "-m" and args:
            paragraphs.append(args.pop(0))
        elif arg == "--push":
            push = True
        else:
            raise Refused(f"{arg!r} is not understood here. {USAGE}")
    raise Refused(f"No paths: name them after --. {USAGE}")


def read_message(repo, message_file, paragraphs):
    if message_file is not None and paragraphs:
        raise Refused("Give the message with -F or with -m, not both.")
    if message_file is not None:
        try:
            text = Path(message_file).read_text(encoding="utf-8")
        except OSError as error:
            raise Refused(f"The message file could not be read: {error}.")
    else:
        text = "\n\n".join(paragraphs)
    cleaned = git(repo, "stripspace", "--strip-comments", input=text)
    if cleaned.returncode != 0:
        raise Refused(f"git could not read the message: {cleaned.stderr.strip()}")
    return cleaned.stdout


def changed_files(repo, base, paths, cwd):
    """The files to commit under each named path, relative to the repository and / separated."""
    root = Path(repo).resolve()
    found = []
    for given in paths:
        try:
            # Non-strict, so a deleted path resolves through the folders that still exist.
            relative = (Path(cwd) / given).resolve().relative_to(root).as_posix()
        except ValueError:
            raise Refused(f"{given} is outside the repository.")
        if relative == "." or relative.split("/")[0] == ".git":
            raise Refused(f"{given}: name the files or folders to commit, not the repository itself.")
        tracked = names(git(repo, "diff", "--name-only", "--no-renames", "-z", base, "--", relative))
        new = names(git(repo, "ls-files", "--others", "--exclude-standard", "-z", "--", relative))
        if not tracked and not new:
            ignored = names(git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "-z", "--", relative))
            if ignored:
                raise Refused(f"{given} is gitignored; it is not committed.")
            raise Refused(f"{given} has no change against HEAD; nothing to commit there.")
        found += [name for name in tracked + new if name not in found]
    return found


def foreign_stage(repo, files):
    """The files staged in the real index with content that differs from the working tree."""
    staged = set(names(git(repo, "diff", "--cached", "--name-only", "--no-renames", "-z", "--", *files)))
    unstaged = set(names(git(repo, "diff", "--name-only", "--no-renames", "-z", "--", *files)))
    return [name for name in files if name in staged and name in unstaged]


def load_config(repo):
    try:
        return json.loads((Path(repo) / "tools" / "leanground.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def build(repo, base, files, message, config):
    """Commits files onto base through a temporary index; returns the new commit's hash or raises Refused."""
    problems = commit_msg.problems(message, config.get("commit_trailer", True), config.get("commit_body", False))
    if problems:
        raise Refused("the message is rejected: " + "; ".join(problems) + ' (CLAUDE.md, "Commits")')
    index = git(repo, "rev-parse", "--git-path", f"lg-commit-index-{os.getpid()}").stdout.strip()
    index = str(Path(repo) / index) if not os.path.isabs(index) else index
    env = dict(os.environ, GIT_INDEX_FILE=index)
    try:
        read = git(repo, "read-tree", base, env=env) if base != EMPTY_TREE else git(repo, "read-tree", "--empty", env=env)
        if read.returncode != 0:
            raise Refused(f"HEAD could not be read into a temporary index: {read.stderr.strip()}")
        added = git(repo, "update-index", "--add", "--remove", "-z", "--stdin", env=env, input="\0".join(files) + "\0")
        if added.returncode != 0:
            raise Refused(f"the paths could not be put in the temporary index: {added.stderr.strip()}")
        hook = Path(repo) / "tools" / "pre_commit.py"
        if hook.is_file():
            checked = subprocess.run([sys.executable, str(hook), str(repo)], cwd=repo, capture_output=True,
                                     encoding="utf-8", errors="replace", env=env)
            if checked.returncode != 0:
                raise Refused("the pre-commit check refused it:\n" + (checked.stdout + checked.stderr).rstrip())
        tree = git(repo, "write-tree", env=env)
        if tree.returncode != 0:
            raise Refused(f"git could not write the tree: {tree.stderr.strip()}")
        if tree.stdout.strip() == git(repo, "rev-parse", f"{base}^{{tree}}").stdout.strip():
            raise Refused("the named paths are as HEAD holds them; nothing to commit")
        parent = [] if base == EMPTY_TREE else ["-p", base]
        made = git(repo, "commit-tree", tree.stdout.strip(), *parent, "-F", "-", input=message)
        if made.returncode != 0:
            raise Refused(f"git commit-tree failed: {made.stderr.strip()}")
    finally:
        for leftover in (index, index + ".lock"):
            if os.path.exists(leftover):
                os.remove(leftover)
    sha = made.stdout.strip()
    subject = message.splitlines()[0]
    # The branch moves only from base, so a commit another session made meanwhile is never overwritten.
    old = base if base != EMPTY_TREE else "0" * len(sha)
    moved = git(repo, "update-ref", "-m", f"commit: {subject}", "HEAD", sha, old)
    if moved.returncode != 0:
        raise Refused("HEAD moved while the commit was built (another session committed); run it again")
    return sha


def main(argv, repo, cwd=None):
    repo = Path(repo)
    cwd = Path.cwd() if cwd is None else Path(cwd)
    try:
        message_file, paragraphs, push, paths = parse(argv)
        if not paths:
            raise Refused(f"No paths: name them after --. {USAGE}")
        config = load_config(repo)
        message = read_message(repo, message_file, paragraphs)
        head = git(repo, "rev-parse", "--verify", "-q", "HEAD")
        base = head.stdout.strip() if head.returncode == 0 else EMPTY_TREE
        files = changed_files(repo, base, paths, cwd)
        clash = foreign_stage(repo, files)
        if clash:
            raise Refused(f"staged in the shared index with content that differs from the working tree, by another"
                          f" session or by you: {', '.join(clash)}. Commit them with the session that staged them,"
                          " or unstage them first")
        sha = build(repo, base, files, message, config)
    except Refused as refusal:
        print(f"commit.py refused, nothing changed: {refusal}".rstrip(".") + ".")
        return 1

    subject = message.splitlines()[0]
    line = f"{sha[:7]} {subject} ({', '.join(files)})"
    synced = git(repo, "reset", "-q", "--", *files)
    if synced.returncode != 0:
        print(line)
        print(f"Committed, but the real index was not brought up to date ({synced.stderr.strip()}); run"
              f" git reset -q -- {' '.join(files)}")
        return 2
    if push and config.get("push_on_commit", False):
        pushed = git(repo, "push", "-q")
        if pushed.returncode != 0:
            print(line)
            print(f"Committed, but the push failed: {pushed.stderr.strip()}")
            return 2
        line += ", pushed"
    elif push:
        line += ', not pushed: "push_on_commit" is false'
    print(line)
    return 0


if __name__ == "__main__":
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, encoding="utf-8")
    sys.exit(main(sys.argv[1:], top.stdout.strip() if top.returncode == 0 else Path(__file__).resolve().parent.parent))
