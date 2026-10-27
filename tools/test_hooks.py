"""Tests for the hooks: tools/search_gate.py, tools/edit_gate.py, tools/stop_check.py and tools/commit_msg.py.
Run from the repository root:

    python -m unittest tools/test_hooks.py
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit_msg  # noqa: E402
import edit_gate  # noqa: E402
import search_gate  # noqa: E402
import stop_check  # noqa: E402


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, encoding="utf-8", check=True).stdout


class Repo(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        self.put("tools/leanground.json", json.dumps({"source_roots": ["app"], "long_file_lines": 5, "branch": "main"}))
        self.put(".gitignore", "ignored.txt\n")
        self.put("DESIGN.md", "# Design\n")
        self.put("app/main.py", "x = 1\n")
        self.commit()

    def put(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "x")


def shell(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


class SearchGate(Repo):
    def refused(self, event):
        return search_gate.refusal(event, self.repo)

    def test_shell_readers_on_tracked_files(self):
        self.assertIsNotNone(self.refused(shell("grep -n foo DESIGN.md")))
        self.assertIsNotNone(self.refused(shell("cd x && cat app/main.py")))
        self.assertIsNotNone(self.refused({"tool_name": "PowerShell", "tool_input": {"command": "Get-Content docs/a.md"}}))

    def test_logs_pipes_and_build_output_pass(self):
        self.assertIsNone(self.refused(shell("git log | grep foo")))
        self.assertIsNone(self.refused(shell("grep ERROR build/logs/latest.log")))
        self.assertIsNone(self.refused(shell("git grep -n foo -- DESIGN.md")))

    def test_a_long_source_file_read_whole(self):
        self.put("app/long.py", "x = 1\n" * 10)
        read = {"tool_name": "Read", "tool_input": {"file_path": str(self.repo / "app/long.py")}}
        self.assertIn("sig long", self.refused(read))
        read["tool_input"]["limit"] = 10
        self.assertIsNone(self.refused(read))
        self.assertIsNone(self.refused({"tool_name": "Read", "tool_input": {"file_path": str(self.repo / "app/main.py")}}))

    def test_a_long_file_outside_the_repository(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (outside / "long.py").write_text("x = 1\n" * 10, encoding="utf-8")
        self.assertIsNone(self.refused({"tool_name": "Read", "tool_input": {"file_path": str(outside / "long.py")}}))


class EditGate(Repo):
    def refused(self, command):
        found = edit_gate.refusal(shell(command), self.repo)
        return found[0] if found else None

    def test_sed_in_place(self):
        self.assertIn("sed -i", self.refused("sed -i 's/a/b/' app/main.py"))
        self.assertIsNone(self.refused("sed 's/a/b/' app/main.py"))
        self.assertIsNone(self.refused('grep -rn "sed -i" app/'))

    def test_redirects(self):
        self.assertIn("redirect", self.refused("echo x > app/main.py"))
        self.assertIn("redirect", self.refused("echo x | tee DESIGN.md"))
        self.assertIsNone(self.refused("echo x > app/new.py"))
        self.put("ignored.txt", "x")
        self.assertIsNone(self.refused("echo x > ignored.txt"))
        self.assertIsNone(self.refused("make 2>&1 > /dev/null"))

    def test_a_variable_is_expanded(self):
        self.assertIn("redirect", self.refused('F=app/main.py; echo x > "$F"'))

    def test_inline_scripts(self):
        heredoc = "python - <<'PY'\nfrom pathlib import Path\nPath('app/main.py').write_text('y')\nPY"
        self.assertIn("script", self.refused(heredoc))
        self.assertIsNone(self.refused("grep -n 'write_text' app/main.py"))

    def test_a_commit_message_heredoc_is_prose(self):
        self.assertIsNone(self.refused("git commit -F - <<'EOF'\nStop using sed -i on app/main.py\nEOF"))

    def test_unreviewed_and_committed_scripts(self):
        self.put("fix.py", "from pathlib import Path\nPath('app/main.py').write_text('y')\n")
        self.assertIn("unreviewed script", self.refused("python fix.py"))
        self.commit()
        self.assertIsNone(self.refused("python fix.py"))

    def test_opting_out(self):
        self.assertIsNone(self.refused("ALLOW_SHELL_EDITS=1 echo x > app/main.py"))
        self.put(".claude/allow-shell-edits", "")
        self.assertIsNone(self.refused("echo x > app/main.py"))

    def test_outside_a_repository(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (outside / "a.py").write_text("x", encoding="utf-8")
        self.assertIsNone(edit_gate.refusal(shell("echo x > a.py"), outside))


class StopCheck(Repo):
    def test_clean_changed_and_ahead(self):
        self.assertIsNone(stop_check.reminder(self.repo))
        self.put("DESIGN.md", "# Changed\n")
        self.assertIn("uncommitted tracked changes", stop_check.reminder(self.repo))
        remote = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, remote, ignore_errors=True)
        git(remote, "init", "-q", "--bare")
        git(self.repo, "remote", "add", "origin", str(remote))
        git(self.repo, "push", "-q", "-u", "origin", "main")
        self.commit()
        self.assertEqual("Reminder: unpushed commits. Commit at a logical checkpoint and push to main as CLAUDE.md"
                         ' "Commits" says, once the build and python tools/docs.py check pass. (tools/stop_check.py)',
                         stop_check.reminder(self.repo))

    def test_untracked_files_are_not_a_reminder(self):
        self.put("scratch.txt", "x")
        self.assertIsNone(stop_check.reminder(self.repo))


class CommitMessage(unittest.TestCase):
    def test_trailer(self):
        good = "Add search\n\nBecause.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
        self.assertEqual([], commit_msg.problems(good))
        self.assertEqual(1, len(commit_msg.problems("Add search\n")))
        self.assertEqual([], commit_msg.problems("Add search\n", require_trailer=False))
        self.assertEqual(1, len(commit_msg.problems("Add search\n\nCo-Authored-By: Claude <bad>\n")))

    def test_body(self):
        bare = "Add search\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
        self.assertEqual([], commit_msg.problems(bare))
        self.assertEqual(1, len(commit_msg.problems(bare, require_body=True)))
        self.assertEqual(1, len(commit_msg.problems("# only a comment\n")))


if __name__ == "__main__":
    unittest.main()
