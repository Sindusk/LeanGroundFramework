"""Tests for the hooks: tools/search_gate.py, tools/edit_gate.py, tools/stop_check.py, tools/commit_msg.py and
tools/pre_commit.py. Run from the repository root:

    python -m unittest tools/test_hooks.py
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import commit_msg  # noqa: E402
import edit_gate  # noqa: E402
import pre_commit  # noqa: E402
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
        self.put("docs/a.md", "a\n")
        self.commit()
        self.assertIsNotNone(self.refused(shell("grep -n foo DESIGN.md")))
        self.assertIsNotNone(self.refused(shell("cd x && cat app/main.py")))
        self.assertIsNotNone(self.refused({"tool_name": "PowerShell", "tool_input": {"command": "Get-Content docs/a.md"}}))
        self.assertIsNotNone(self.refused(shell(f"cd \"{self.repo / 'docs'}\"; cat a.md")))
        self.assertIsNotNone(self.refused(shell(f"cat \"{self.repo / 'DESIGN.md'}\"")))
        self.assertIsNotNone(self.refused(shell("grep -rn foo docs/")))

    def test_untracked_ignored_and_outside_files_pass(self):
        self.put(".gitignore", "ignored.txt\n/scratch/\n/run/\n")
        self.put("scratch/pending/brief.md", "b\n")
        self.put("run/server/config/a.json", "{}\n")
        self.commit()
        self.assertIsNone(self.refused(shell("cat scratch/pending/brief.md")))
        self.assertIsNone(self.refused(shell("cd run/server && cat config/a.json")))
        self.assertIsNone(self.refused(shell("cat 'run/server/config/a.json'")))
        self.assertIsNone(self.refused(shell("cat docs/missing.md")))
        self.put("notes/new.md", "n\n")
        self.assertIsNone(self.refused(shell("cat notes/new.md")))
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (outside / "DESIGN.md").write_text("x\n", encoding="utf-8")
        self.assertIsNone(self.refused(shell(f"cd \"{outside}\" && grep -n x DESIGN.md")))
        self.assertIsNone(self.refused(shell(f"grep -n x \"{outside / 'DESIGN.md'}\"")))

    def test_absolute_path_with_punctuation(self):
        path = "notes!#sample/README.md"
        self.put(path, "# Notes\n")
        self.commit()
        self.assertIsNotNone(self.refused({"tool_name": "PowerShell",
                                           "tool_input": {"command": f"Get-Content '{self.repo / path}'"}}))
        self.assertIsNotNone(self.refused(shell(f"cat \"{self.repo / path}\"")))

    def test_a_quoted_path_with_spaces(self):
        self.put("notes/two words.md", "x\n")
        self.commit()
        self.assertIsNotNone(self.refused(shell('cat "notes/two words.md"')))
        self.assertIsNotNone(self.refused({"tool_name": "PowerShell",
                                           "tool_input": {"command": "Get-Content 'notes/two words.md' -TotalCount 5"}}))

    def test_whole_disk_searches(self):
        for command in ('find / -iname "*report*.pdf" 2>/dev/null | head -3', "cd x && find /c -name a",
                        "find ~ -name a", "find C:/ -name a", "ls run; find /c/Users -name x", "find $HOME -name a",
                        "ls -R /"):
            self.assertIsNotNone(self.refused(shell(command)), command)
        for command in ("Get-ChildItem C:\\ -Recurse -Filter *.pdf", "gci -r ~ -Filter a", "dir C:\\ /s /b"):
            self.assertIsNotNone(self.refused({"tool_name": "PowerShell", "tool_input": {"command": command}}), command)
        for command in ('find run/server -path "*config*" -name a', "find . -name x", "ls /", "git grep find",
                        "ls ~", "find docs -name '*.md'"):
            self.assertIsNone(self.refused(shell(command)), command)
        self.assertIsNone(self.refused({"tool_name": "PowerShell", "tool_input": {"command": "Get-ChildItem run -Recurse"}}))

    def test_shell_read_paths_pass_and_nothing_else(self):
        self.put("tools/leanground.json", json.dumps({"shell_read_paths": ["docs/data/*.txt", "tools/allow.txt"]}))
        self.put("docs/data/sample-01.txt", "x\n")
        self.put("docs/data/sample-02.txt", "x\n")
        self.put("docs/data/sample-01.md", "sheet\n")
        self.put("tools/allow.txt", "x\n")
        self.commit()
        self.assertIsNone(self.refused(shell("cat docs/data/sample-01.txt tools/allow.txt; python x.py")))
        self.assertIsNone(self.refused(shell('cat "docs\\data\\sample-02.txt"')))
        self.assertIsNotNone(self.refused(shell("cat docs/data/sample-01.txt docs/data/sample-01.md")))
        self.assertIsNotNone(self.refused(shell("grep -n foo DESIGN.md")))

    def test_logs_pipes_and_build_output_pass(self):
        self.assertIsNone(self.refused(shell("git log | grep foo")))
        self.assertIsNone(self.refused(shell("grep ERROR build/logs/latest.log")))
        self.assertIsNone(self.refused(shell("git grep -n foo -- DESIGN.md")))
        self.assertIsNone(self.refused(shell('grep ERROR "build/logs/latest.log"')))
        self.assertIsNotNone(self.refused(shell("grep ERROR build/logs/latest.log DESIGN.md")))

    def test_line_windows_over_the_limit(self):
        self.put("app/long.py", "x = 1\n" * 300)
        self.put("docs/notes.md", "line\n" * 300)
        self.commit()
        for command in ("sed -n '1,200p' app/long.py", 'sed -n "100,+80p" docs/notes.md', "sed -n '200,$p' app/long.py",
                        "sed -ne '1,40p;100,140p' app/long.py", "head -n 100 app/long.py", "head -100 docs/notes.md",
                        "head --lines=61 app/long.py", "tail -n 80 app/long.py", "tail -n +200 app/long.py",
                        "awk 'NR>=10 && NR<=200' app/long.py", "awk 'NR>100' docs/notes.md",
                        "awk 'NR==10,NR==90' app/long.py", "cd docs && sed -n '1,100p' notes.md"):
            reason = self.refused(shell(command))
            self.assertIsNotNone(reason, command)
            self.assertIn("shell_window_lines", reason)
        self.assertIn("docs.py sig <Name>", self.refused(shell("head -n 100 app/long.py")))
        self.assertIn("prints 191 lines of app/long.py", self.refused(shell("awk 'NR>=10 && NR<=200' app/long.py")))

    def test_small_windows_and_other_reads_pass(self):
        self.put("app/long.py", "x = 1\n" * 300)
        self.put(".gitignore", "ignored.txt\n/run/\n")
        self.put("run/server.log", "x\n" * 300)
        self.commit()
        for command in ("sed -n '10,69p' app/long.py", "head -n 60 app/long.py", "head app/long.py", "tail -5 app/long.py",
                        "tail -n +250 app/long.py", "awk 'NR>=10 && NR<=60' app/long.py", "sed -n '5p' app/long.py",
                        "git log | head -n 500", "python x.py | tail -n 200", "tail -n 200 run/server.log",
                        "head -n 200 build/out.txt", "sed 's/a/b/' app/long.py", "awk '{print $1}' app/long.py",
                        "tail -f app/long.py", "head -c 9000 app/long.py", "sed -n '/def /p' app/long.py"):
            self.assertIsNone(self.refused(shell(command)), command)

    def test_a_window_on_a_shell_read_path_passes(self):
        self.put("tools/leanground.json", json.dumps({"shell_read_paths": ["docs/data/*.md"], "shell_window_lines": 10}))
        self.put("docs/data/table.md", "row\n" * 100)
        self.put("docs/other.md", "row\n" * 100)
        self.commit()
        self.assertIsNone(self.refused(shell("head -n 50 docs/data/table.md")))
        self.assertIn("over 10", self.refused(shell("head -n 50 docs/other.md")))
        self.assertIsNone(self.refused(shell("head -n 10 docs/other.md")))

    def test_an_equals_sign_is_part_of_a_path_but_not_of_an_option(self):
        self.put("docs/a=b.md", "x\n")
        self.commit()
        self.assertIsNotNone(self.refused(shell("cat docs/a=b.md")))
        self.assertIsNotNone(self.refused(shell("grep --file=DESIGN.md x")))
        base = str(self.repo)
        self.assertEqual(os.path.normpath(os.path.join(base, "docs/a=b.md")), search_gate.as_path("docs/a=b.md", base))
        self.assertEqual(os.path.normpath(os.path.join(base, "x.md")), search_gate.as_path("--file=x.md", base))

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
        self.assertIn("script", self.refused("python -c \"open('app/main.py', 'w').write('y')\""))

    def test_a_path_beside_an_inline_script_is_not_its_target(self):
        heredoc = "python - <<'PY'\nfrom pathlib import Path\nPath('/tmp/x').write_text('y')\nPY\npython -m unittest app/main.py"
        self.assertIsNone(self.refused(heredoc))
        self.assertIsNone(self.refused("python -c \"open('x.log', 'w')\"; python -m unittest app/main.py"))

    def test_a_quoted_path_with_spaces(self):
        self.put("notes/two words.md", "x\n")
        self.commit()
        self.assertIn("redirect", self.refused('echo x > "notes/two words.md"'))
        self.assertIn("redirect", self.refused("echo x | tee -a 'notes/two words.md'"))
        self.assertIn("script", self.refused("python -c \"open('notes/two words.md', 'w').write('y')\""))
        self.assertIsNone(self.refused('git commit -m "fix the notes/two words.md typo"'))

    def test_a_commit_message_heredoc_is_prose(self):
        self.assertIsNone(self.refused("git commit -F - <<'EOF'\nStop using sed -i on app/main.py\nEOF"))

    def test_unreviewed_and_committed_scripts(self):
        self.put("fix.py", "from pathlib import Path\nPath('app/main.py').write_text('y')\n")
        self.assertIn("unreviewed script", self.refused("python fix.py"))
        self.assertIsNone(self.refused("git add app/main.py fix.py"))
        self.put("tool.py", '"""Reads app/main.py."""\nfrom pathlib import Path\nPath("run/out.txt").write_text("y")\n')
        self.assertIsNone(self.refused("python tool.py"))
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
        # An upstream written as a local ref, so the test never runs git's push transport (refused on some hosts).
        git(self.repo, "remote", "add", "origin", str(self.repo / "no-such-remote"))
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(self.repo, "branch", "--set-upstream-to=origin/main", "main")
        self.commit()
        self.assertEqual("Reminder: unpushed commits. Commit at a logical checkpoint and push to main as CLAUDE.md"
                         ' "Commits" says, once the build and python tools/docs.py check pass. (tools/stop_check.py)',
                         stop_check.reminder(self.repo))

    def test_untracked_files_are_not_a_reminder(self):
        self.put("scratch.txt", "x")
        self.assertIsNone(stop_check.reminder(self.repo))


FAILING_CHECK = ("import pathlib, sys\npathlib.Path('ignored.txt').write_text('ran')\n"
                 "print('  LEDGER.md:1  a stub problem')\nprint('1 problems.')\nsys.exit(1)\n")
KIT = Path(__file__).resolve().parent.parent


class PreCommit(Repo):
    def setUp(self):
        super().setUp()
        self.put("tools/docs.py", FAILING_CHECK)
        self.commit()

    def run_hook(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = pre_commit.main(self.repo)
        return code, err.getvalue()

    def test_the_guarded_files(self):
        staged = ["app/main.py", ".claude/skills/x/SKILL.md", "LEDGER.md", "DESIGN.md", "notes/x.md", "CLAUDE.md",
                  "AGENTS.md", "docs/other.md"]
        self.assertEqual([".claude/skills/x/SKILL.md", "LEDGER.md", "DESIGN.md", "notes/x.md", "CLAUDE.md", "AGENTS.md"],
                         pre_commit.guarded(staged, {"notes/x.md": 100}))

    def test_check_runs_only_for_a_guarded_file(self):
        self.put("app/main.py", "x = 2\n")
        git(self.repo, "add", "-A")
        self.assertEqual((0, ""), self.run_hook())
        self.assertFalse((self.repo / "ignored.txt").exists())
        self.put(".claude/agents/a.md", "# A\n")
        git(self.repo, "add", "-A")
        code, err = self.run_hook()
        self.assertEqual(1, code)
        self.assertIn("Commit refused: it stages .claude/agents/a.md", err)
        self.assertIn("LEDGER.md:1  a stub problem", err)
        self.put("tools/docs.py", "print('Everything resolves.')\n")
        git(self.repo, "add", "-A")
        self.assertEqual((0, ""), self.run_hook())

    def test_a_real_commit_through_the_hook(self):
        shutil.copy(KIT / ".githooks" / "pre-commit", self.repo / "hooks-pre-commit")
        (self.repo / "hooks").mkdir()
        shutil.move(self.repo / "hooks-pre-commit", self.repo / "hooks" / "pre-commit")
        shutil.copy(KIT / "tools" / "pre_commit.py", self.repo / "tools" / "pre_commit.py")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "Hooks")
        git(self.repo, "config", "core.hooksPath", "hooks")
        self.put("DESIGN.md", "# Changed\n")
        git(self.repo, "add", "-A")
        refused = subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=self.repo, capture_output=True, encoding="utf-8")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("a stub problem", refused.stderr)
        git(self.repo, "reset", "-q", "--hard")
        self.put("app/main.py", "x = 3\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "Untouched")


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

    def test_a_body_line_shaped_like_a_trailer_is_body(self):
        trailer = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
        self.assertEqual([], commit_msg.problems(f"Add search\n\nVerification: offline tests\n\n{trailer}",
                                                 require_body=True))
        self.assertEqual([], commit_msg.problems(f"Add search\n\nNote: why.\nMore prose.\n\n{trailer}", require_body=True))
        self.assertEqual(1, len(commit_msg.problems(f"Add search\n\nSigned-off-by: A <a@b.c>\n{trailer}",
                                                    require_body=True)))


if __name__ == "__main__":
    unittest.main()
