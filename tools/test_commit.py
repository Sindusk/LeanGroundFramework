"""Tests for tools/commit.py, committing named paths through a temporary index, against real temporary
repositories. Run from the repository root:

    python -m unittest tools/test_commit.py
"""

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit  # noqa: E402

KIT = Path(__file__).resolve().parent.parent
TRAILER = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
FAILING_CHECK = "print('  DESIGN.md:1  a stub problem')\nraise SystemExit(1)\n"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, encoding="utf-8", check=True).stdout


class Commit(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        self.configure(commit_trailer=False)
        self.put(".gitignore", "/working/\n")
        self.put("DESIGN.md", "# Design\n")
        self.put("app/main.py", "x = 1\n")
        self.put("app/other.py", "y = 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "Start")
        self.start = self.head()

    def configure(self, **settings):
        self.put("tools/leanground.json", json.dumps(settings))

    def put(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def head(self):
        return git(self.repo, "rev-parse", "HEAD").strip()

    def committed(self):
        return git(self.repo, "diff-tree", "--no-commit-id", "--name-status", "-r", "HEAD").split("\n")[:-1]

    def staged(self):
        return git(self.repo, "diff", "--cached", "--name-only").split()

    def status(self, *paths):
        return git(self.repo, "status", "--porcelain", "--", *paths)

    def run_commit(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = commit.main(list(args), self.repo, cwd=self.repo)
        return code, out.getvalue()

    def test_only_the_named_paths_while_another_is_staged(self):
        self.put("app/main.py", "x = 2\n")
        self.put("app/other.py", "y = 2\n")
        git(self.repo, "add", "app/other.py")
        self.put("DESIGN.md", "# Changed elsewhere\n")
        code, out = self.run_commit("-m", "Change main", "--", "app/main.py")
        self.assertEqual(0, code, out)
        self.assertEqual(f"{self.head()[:7]} Change main (app/main.py)\n", out)
        self.assertEqual(["M\tapp/main.py"], self.committed())
        self.assertEqual(self.start, git(self.repo, "rev-parse", "HEAD~1").strip())
        self.assertEqual(["app/other.py"], self.staged())
        self.assertEqual("", self.status("app/main.py"))
        self.assertEqual(" M DESIGN.md\n", self.status("DESIGN.md"))
        self.assertEqual("y = 2\n", git(self.repo, "show", ":app/other.py"))

    def test_a_new_file_and_a_folder(self):
        self.put("notes/new.md", "new\n")
        self.put("app/more/a.py", "a\n")
        self.put("app/main.py", "x = 2\n")
        self.put("working/scratch.md", "s\n")
        message = self.repo / "working" / "message.txt"
        message.write_text("New notes\n\nWhy.\n", encoding="utf-8")
        code, out = self.run_commit("-F", str(message), "--", "notes/new.md", "app")
        self.assertEqual(0, code, out)
        self.assertEqual(["A\tapp/more/a.py", "A\tnotes/new.md", "M\tapp/main.py"], sorted(self.committed()))
        self.assertEqual("New notes\n\nWhy.\n", git(self.repo, "log", "-1", "--format=%B").rstrip("\n") + "\n")
        self.assertEqual("", self.status("notes", "app"))
        self.assertEqual([], self.staged())

    def test_a_deletion(self):
        (self.repo / "app" / "other.py").unlink()
        code, out = self.run_commit("-m", "Drop other", "--", "app/other.py")
        self.assertEqual(0, code, out)
        self.assertEqual(["D\tapp/other.py"], self.committed())
        self.assertEqual("", self.status())

    def test_refuses_a_foreign_staged_path(self):
        self.put("app/main.py", "x = 2\n")
        git(self.repo, "add", "app/main.py")
        self.put("app/main.py", "x = 3\n")
        code, out = self.run_commit("-m", "Mine", "--", "app/main.py")
        self.assertEqual(1, code)
        self.assertIn("staged in the shared index with content that differs", out)
        self.assertEqual(self.start, self.head())
        self.assertEqual("x = 2\n", git(self.repo, "show", ":app/main.py"))
        # Staged as the working tree holds it is no other session's work: it is committed.
        git(self.repo, "add", "app/main.py")
        self.assertEqual(0, self.run_commit("-m", "Mine", "--", "app/main.py")[0])
        self.assertEqual("", self.status())

    def test_refuses_when_nothing_changed(self):
        code, out = self.run_commit("-m", "Nothing", "--", "app/main.py")
        self.assertEqual(1, code)
        self.assertIn("app/main.py has no change against HEAD", out)
        git(self.repo, "rm", "-q", "--cached", "app/other.py")
        self.assertIn("as HEAD holds them", self.run_commit("-m", "Same", "--", "app/other.py")[1])
        self.assertEqual(self.start, self.head())
        git(self.repo, "reset", "-q", "--", "app/other.py")
        self.put("app/main.py", "x = 2\n")
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        for args, reason in ((["--", "app/main.py", "app/other.py"], "app/other.py has no change"),
                             (["--", str(outside / "a.txt")], "outside the repository"),
                             (["--", "../elsewhere.txt"], "outside the repository"),
                             (["--", "working/scratch.md"], "has no change"),
                             (["app/main.py"], "is not understood"),
                             (["--"], "No paths")):
            code, out = self.run_commit("-m", "Refused", *args)
            self.assertEqual(1, code, args)
            self.assertIn(reason, out, args)
        self.put("working/scratch.md", "s\n")
        self.assertIn("gitignored", self.run_commit("-m", "x", "--", "working/scratch.md")[1])
        code, out = self.run_commit("-m", "  ", "--", "app/main.py")
        self.assertEqual(1, code)
        self.assertIn("the commit message is empty", out)
        self.assertEqual(self.start, self.head())
        self.assertEqual([], self.staged())

    def test_the_trailer_rule_still_applies(self):
        self.configure(commit_trailer=True)
        git(self.repo, "commit", "-q", "-am", f"Trailer on\n\n{TRAILER}")
        start = self.head()
        self.put("app/main.py", "x = 2\n")
        code, out = self.run_commit("-m", "No trailer", "--", "app/main.py")
        self.assertEqual(1, code)
        self.assertIn("Co-Authored-By", out)
        self.assertEqual(start, self.head())
        self.assertEqual(0, self.run_commit("-m", "With trailer", "-m", TRAILER, "--", "app/main.py")[0])
        self.assertEqual(f"With trailer\n\n{TRAILER}", git(self.repo, "log", "-1", "--format=%B").strip())

    def test_the_pre_commit_check_judges_only_this_commit(self):
        shutil.copy(KIT / "tools" / "pre_commit.py", self.repo / "tools" / "pre_commit.py")
        self.put("tools/docs.py", FAILING_CHECK)
        git(self.repo, "add", "tools")
        git(self.repo, "commit", "-q", "-m", "Hook")
        start = self.head()
        self.put("DESIGN.md", "# Staged by another session\n")
        git(self.repo, "add", "DESIGN.md")
        self.put("app/main.py", "x = 2\n")
        self.assertEqual(0, self.run_commit("-m", "Code only", "--", "app/main.py")[0])
        self.assertEqual(["DESIGN.md"], self.staged())
        code, out = self.run_commit("-m", "Design", "--", "DESIGN.md")
        self.assertEqual(1, code)
        self.assertIn("a stub problem", out)
        self.assertEqual(start, git(self.repo, "rev-parse", "HEAD~1").strip())

    def test_a_moved_head_is_never_overwritten(self):
        self.put("app/main.py", "x = 2\n")
        self.put("app/other.py", "y = 2\n")
        self.assertEqual(0, self.run_commit("-m", "Another session", "--", "app/other.py")[0])
        moved = self.head()
        with self.assertRaises(commit.Refused):
            commit.build(self.repo, self.start, ["app/main.py"], "Stale\n", {"commit_trailer": False})
        self.assertEqual(moved, self.head())

    def test_push(self):
        self.put("app/main.py", "x = 2\n")
        code, out = self.run_commit("-m", "No push", "--push", "--", "app/main.py")
        self.assertEqual(0, code)
        self.assertIn('not pushed: "push_on_commit" is false', out)
        self.configure(commit_trailer=False, push_on_commit=True)
        git(self.repo, "commit", "-q", "-am", "Push on")
        self.put("app/main.py", "x = 3\n")
        code, out = self.run_commit("-m", "Push, no remote", "--push", "--", "app/main.py")
        self.assertEqual(2, code)
        self.assertIn("Committed, but the push failed", out)
        self.assertEqual("", self.status("app/main.py"))

    def test_the_first_commit_of_a_repository(self):
        fresh = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, fresh, ignore_errors=True)
        git(fresh, "init", "-q", "-b", "main")
        git(fresh, "config", "user.email", "test@example.com")
        git(fresh, "config", "user.name", "Test")
        (fresh / "a.txt").write_text("a\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, commit.main(["-m", "First", "-m", TRAILER, "--", "a.txt"], fresh, cwd=fresh))
        self.assertEqual("a.txt\n", git(fresh, "ls-files"))
        self.assertEqual("", git(fresh, "status", "--porcelain"))


if __name__ == "__main__":
    unittest.main()
