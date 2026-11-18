"""Tests for tools/upgrade.py, taking a newer kit's core files into a project, against real temporary
repositories: a kit with two commits and a project taken from the first. Run from the repository root:

    python -m unittest tools/test_upgrade.py
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

import upgrade  # noqa: E402

CHECK = "print('Everything resolves.')\n"
PASSING = "import unittest\n\n\nclass Fine(unittest.TestCase):\n    def test_fine(self):\n        pass\n"
TEMPLATE = ("---\nname: {0}\ndescription: Builds packages.\n---\n\n# {0}\n\nAsk the lg-design skill;"
            " see .claude/skills/{0}/cut.md. Not lg-packages, lg-package-x or xlg-package.\n")
SKILL, RENAMED = TEMPLATE.format("lg-package"), TEMPLATE.format("mm-package")


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, encoding="utf-8", check=True).stdout


def settings(**extra):
    base = {"bootstrapped": True, "long_file_lines": 400, "handoff_past": 200000, "core_paths": {},
            "kit_version": "", "budgets": {".claude/skills/lg-package/SKILL.md": 900},
            "core": ["tools/docs.py", "tools/test_ok.py", "tools/a.py", ".claude/skills/lg-package/", ".githooks/"]}
    base.update(extra)
    return base


class Upgrade(unittest.TestCase):
    def setUp(self):
        self.kit = self.repository()
        self.project = self.repository()
        self.put(self.kit, "tools/leanground.json", json.dumps(settings(), indent=2) + "\n")
        self.put(self.kit, "tools/docs.py", CHECK)
        self.put(self.kit, "tools/test_ok.py", PASSING)
        self.put(self.kit, "tools/a.py", "a = 1\n")
        self.put(self.kit, ".claude/skills/lg-package/SKILL.md", SKILL)
        self.put(self.kit, ".githooks/commit-msg", "#!/bin/sh\nexit 0\n")
        git(self.kit, "add", "-A")
        git(self.kit, "update-index", "--chmod=+x", ".githooks/commit-msg")
        git(self.kit, "commit", "-q", "-m", "Kit one")
        self.base = git(self.kit, "rev-parse", "HEAD").strip()
        # The project is a copy of the first kit with its own settings and files.
        for name in ("tools/docs.py", "tools/test_ok.py", "tools/a.py", ".claude/skills/lg-package/SKILL.md",
                     ".githooks/commit-msg"):
            self.put(self.project, name, (self.kit / name).read_text(encoding="utf-8"))
        self.configure(project="Demo")
        self.put(self.project, "app/main.py", "x = 1\n")
        self.commit_project("Project")
        # The kit moves on: a changed file, a new file, a dropped file kept nowhere, a new setting.
        self.put(self.kit, "tools/a.py", "a = 2\n")
        self.put(self.kit, "tools/b.py", "b = 1\n")
        self.put(self.kit, "tools/leanground.json", json.dumps(settings(
            section_cap=5000, budgets={".claude/skills/lg-package/SKILL.md": 950, "CLAUDE.md": 1250},
            core=["tools/docs.py", "tools/test_ok.py", "tools/a.py", "tools/b.py", ".claude/skills/lg-package/",
                  ".githooks/"]), indent=2) + "\n")
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-q", "-m", "Kit two")
        self.head = git(self.kit, "rev-parse", "HEAD").strip()

    def repository(self):
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "Test")
        git(repo, "config", "core.autocrlf", "false")
        return repo

    def put(self, repo, name, text):
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def read(self, name):
        return (self.project / name).read_bytes().decode("utf-8")

    def configure(self, **extra):
        values = {"project": "Demo", "long_file_lines": 300, "handoff_past": 150000,
                  "core": ["tools/docs.py", "tools/test_ok.py", "tools/a.py", ".claude/skills/lg-package/",
                           ".githooks/"],
                  "budgets": {".claude/skills/lg-package/SKILL.md": 900}}
        values.update(extra)
        self.put(self.project, "tools/leanground.json", json.dumps(values, indent=4) + "\n")

    def commit_project(self, message):
        git(self.project, "add", "-A")
        git(self.project, "commit", "-q", "-m", message)

    def run_upgrade(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = upgrade.main([str(self.kit), *args], self.project)
        return code, output.getvalue()

    def config(self):
        return json.loads(self.read("tools/leanground.json"))

    def test_a_dry_run_changes_nothing(self):
        code, out = self.run_upgrade("--base", self.base)
        self.assertEqual(0, code, out)
        self.assertIn("Add, new in the kit:\n  tools/b.py\n", out)
        self.assertIn("Replace, changed in the kit and unedited here:\n  tools/a.py\n", out)
        self.assertIn("  add section_cap = 5000", out)
        self.assertTrue(out.rstrip().splitlines()[-1].startswith("Dry run: nothing changed. Next:"))
        self.assertEqual("", git(self.project, "status", "--porcelain"))

    def test_an_apply_replaces_an_unedited_file_adds_a_new_one_and_records_the_version(self):
        code, out = self.run_upgrade("--apply", "--base", self.base)
        self.assertEqual(0, code, out)
        self.assertEqual("a = 2\n", self.read("tools/a.py"))
        self.assertEqual("b = 1\n", self.read("tools/b.py"))
        self.assertEqual("x = 1\n", self.read("app/main.py"))
        self.assertEqual(self.head, self.config()["kit_version"])
        self.assertIn("python tools/docs.py check: Everything resolves.", out)
        self.assertIn("python -m unittest discover -s tools: OK", out)
        self.assertTrue(out.rstrip().splitlines()[-1].startswith("Next: review git diff --stat"))
        self.assertNotIn("app/main.py", git(self.project, "status", "--porcelain"))
        self.assertEqual("", git(self.project, "diff", "--cached", "--name-only"))
        # Recorded, the version is the next run's base: nothing left to do.
        self.commit_project("Upgraded")
        code, out = self.run_upgrade()
        self.assertEqual(0, code, out)
        self.assertIn("Base: " + self.head[:7] + " (the recorded kit_version)", out)
        self.assertIn("Nothing to do", out)

    def test_a_project_edit_is_a_conflict_left_alone_until_theirs(self):
        self.put(self.project, "tools/a.py", "a = 1  # ours\n")
        self.configure(kit_version=self.base)
        self.commit_project("Our edit")
        code, out = self.run_upgrade("--apply")
        self.assertEqual(2, code, out)
        self.assertIn("  tools/a.py: the kit +1 -1 and the project +1 -1 since " + self.base[:7], out)
        self.assertIn("git diff --no-index -- tools/a.py " + (self.kit.resolve() / "tools/a.py").as_posix(), out)
        self.assertIn("Remaining: 1 conflicts", out)
        self.assertEqual("a = 1  # ours\n", self.read("tools/a.py"))
        self.assertEqual("b = 1\n", self.read("tools/b.py"))
        self.assertEqual(self.base, self.config()["kit_version"])
        self.commit_project("Partly upgraded")
        code, out = self.run_upgrade("--apply", "--theirs", "tools/a.py")
        self.assertEqual(0, code, out)
        self.assertEqual("a = 2\n", self.read("tools/a.py"))
        self.assertEqual(self.head, self.config()["kit_version"])

    def test_an_edit_the_kit_never_changed_is_kept(self):
        self.put(self.project, "tools/docs.py", CHECK + "# ours\n")
        self.commit_project("Our docs")
        code, out = self.run_upgrade("--apply", "--base", self.base)
        self.assertEqual(0, code, out)
        self.assertIn("Kept, edited here and unchanged in the kit:\n  tools/docs.py\n", out)
        self.assertEqual(CHECK + "# ours\n", self.read("tools/docs.py"))

    def test_no_recorded_version_makes_differences_possible_conflicts_until_base(self):
        code, out = self.run_upgrade("--apply")
        self.assertEqual(2, code, out)
        self.assertIn("No kit_version is recorded", out)
        self.assertIn("Possible conflicts", out)
        self.assertIn("  tools/a.py: differs from the kit by +1 -1", out)
        self.assertEqual("a = 1\n", self.read("tools/a.py"))
        self.assertEqual("", self.config()["kit_version"])
        self.commit_project("Partly upgraded")
        code, out = self.run_upgrade("--apply", "--base", self.base)
        self.assertEqual(0, code, out)
        self.assertEqual("a = 2\n", self.read("tools/a.py"))

    def test_a_mapped_skill_is_written_under_the_project_name(self):
        shutil.rmtree(self.project / ".claude/skills/lg-package")
        self.put(self.project, ".claude/skills/mm-package/SKILL.md", RENAMED)
        self.put(self.project, ".claude/skills/mm-package/notes.md", "Our own.\n")
        self.configure(core=["tools/docs.py", "tools/a.py", ".claude/skills/mm-package/", ".githooks/"],
                       budgets={".claude/skills/mm-package/SKILL.md": 900})
        self.commit_project("Rename the skill")
        # Unmapped, the skill is held back and the mapping proposed, never copied under the kit's name.
        code, out = self.run_upgrade("--base", self.base)
        self.assertIn('"core_paths": {".claude/skills/lg-package/": ".claude/skills/mm-package/"}', out)
        self.assertNotIn("notes.md", out)
        self.configure(core=["tools/docs.py", "tools/a.py", ".claude/skills/mm-package/", ".githooks/"],
                       budgets={".claude/skills/mm-package/SKILL.md": 900},
                       core_paths={".claude/skills/lg-package/": ".claude/skills/mm-package/"})
        self.commit_project("Map it")
        self.put(self.kit, ".claude/skills/lg-package/SKILL.md", SKILL + "Then the lg-package skill closes.\n")
        git(self.kit, "commit", "-q", "-am", "Kit three")
        code, out = self.run_upgrade("--apply", "--base", self.base)
        self.assertEqual(0, code, out)
        self.assertIn(".claude/skills/mm-package/SKILL.md (from .claude/skills/lg-package/SKILL.md); 4 skill names"
                      " rewritten", out)
        self.assertFalse((self.project / ".claude/skills/lg-package").exists())
        self.assertEqual(RENAMED + "Then the mm-package skill closes.\n",
                         self.read(".claude/skills/mm-package/SKILL.md"))
        self.assertEqual("Our own.\n", self.read(".claude/skills/mm-package/notes.md"))
        self.assertEqual({".claude/skills/mm-package/SKILL.md": 900}, self.config()["budgets"])

    def test_skill_names_are_rewritten_only_where_they_name_a_skill(self):
        names = {"lg-package": "mm-package", "lg-bootstrap": "bootstrap"}
        text = ("the lg-package skill; `lg-package`; lg-package's; lg-packages; lg-package-x; xlg-package;"
                " my-lg-package; lg-package2; skills/lg-bootstrap/; lg-bootstrap.\n")
        self.assertEqual(("the mm-package skill; `mm-package`; mm-package's; lg-packages; lg-package-x; xlg-package;"
                          " my-lg-package; lg-package2; skills/bootstrap/; bootstrap.\n", 5),
                         upgrade.rename_skills(text, names))
        # A plain word is a skill name only in a skill's own places.
        text = ("---\nname: package\n---\n\n# package: retro\n\nThe package skill, the package skill's cut.md and"
                " .claude/skills/package/ build a package; package names, # packages.\n")
        self.assertEqual(("---\nname: lg-package\n---\n\n# lg-package: retro\n\nThe lg-package skill, the lg-package"
                          " skill's cut.md and .claude/skills/lg-package/ build a package; package names,"
                          " # packages.\n", 5), upgrade.rename_skills(text, {"package": "lg-package"}))
        self.assertEqual(("name: a\r\n# a\r\n", 2), upgrade.rename_skills("name: b\r\n# b\r\n", {"b": "a"}))

    def test_settings_gain_missing_keys_and_keep_their_values(self):
        self.configure(subagent_build_past=120000, handoff_past=None)
        values = self.config()
        del values["handoff_past"]
        self.put(self.project, "tools/leanground.json", json.dumps(values, indent=4) + "\n")
        self.put(self.project, "CLAUDE.md", "# Demo\n")
        self.commit_project("Old setting")
        code, out = self.run_upgrade("--apply", "--base", self.base)
        self.assertEqual(0, code, out)
        self.assertIn("add handoff_past = 120000, the value of subagent_build_past, which the kit renamed", out)
        self.assertIn("budgets kept where the kit's differ: .claude/skills/lg-package/SKILL.md here 900, kit 950", out)
        values = self.config()
        # Missing keys land after the key the kit has before them; the old name stays for the owner to delete.
        self.assertEqual(["bootstrapped", "project", "long_file_lines", "handoff_past", "core_paths", "kit_version",
                          "section_cap", "core", "budgets", "subagent_build_past"], list(values))
        self.assertEqual(("Demo", 300, 120000, 5000, 120000), (values["project"], values["long_file_lines"],
                                                                values["handoff_past"], values["section_cap"],
                                                                values["subagent_build_past"]))
        self.assertEqual({".claude/skills/lg-package/SKILL.md": 900, "CLAUDE.md": 1250}, values["budgets"])
        self.assertIn("tools/b.py", values["core"])
        self.assertTrue(self.read("tools/leanground.json").startswith('{\n    "bootstrapped"'))

    def test_a_dirty_target_refuses(self):
        self.put(self.project, "tools/a.py", "a = 1  # unsaved\n")
        code, out = self.run_upgrade("--apply", "--base", self.base, "--theirs", "tools/a.py")
        self.assertEqual(1, code, out)
        self.assertIn("uncommitted changes in files it would write: tools/a.py", out)
        self.assertFalse((self.project / "tools/b.py").exists())
        # A dirty file it would not write is no reason to refuse.
        git(self.project, "checkout", "--", "tools/a.py")
        self.put(self.project, "app/main.py", "x = 2\n")
        self.assertEqual(0, self.run_upgrade("--apply", "--base", self.base)[0])

    def test_named_paths_limit_the_run(self):
        code, out = self.run_upgrade("--apply", "--base", self.base, "tools/b.py")
        self.assertEqual(0, code, out)
        self.assertEqual("b = 1\n", self.read("tools/b.py"))
        self.assertEqual("a = 1\n", self.read("tools/a.py"))
        self.assertNotIn("kit_version", self.config())
        self.assertIn("not a core file", self.run_upgrade("app/main.py")[1])

    def test_a_file_the_kit_dropped_is_removed_only_when_asked(self):
        self.put(self.kit, "tools/leanground.json", json.dumps(settings(
            core=["tools/docs.py", "tools/test_ok.py", "tools/b.py", ".claude/skills/lg-package/",
                  ".githooks/"]), indent=2) + "\n")
        git(self.kit, "commit", "-q", "-am", "Drop a.py")
        code, out = self.run_upgrade("--base", self.base)
        self.assertIn("Not in the kit any more, unedited here (--remove deletes them):\n  tools/a.py: the kit dropped"
                      " it", out)
        code, out = self.run_upgrade("--apply", "--base", self.base, "--remove")
        self.assertEqual(0, code, out)
        self.assertFalse((self.project / "tools/a.py").exists())

    def test_refusals(self):
        for kit, reason in ((self.project, "the kit path is this project"),
                            (self.project / "app", 'holds no tools/leanground.json with a "core" list')):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(1, upgrade.main([str(kit)], self.project))
            self.assertIn(reason, output.getvalue())
        self.assertIn("holds no commit", self.run_upgrade("--base", "nope")[1])
        self.assertIn("is not understood", self.run_upgrade("--force")[1])

    def test_a_project_never_set_up_from_the_kit(self):
        (self.project / "tools/leanground.json").unlink()
        self.commit_project("No settings")
        code, out = self.run_upgrade()
        self.assertEqual(0, code, out)
        self.assertIn("This project has no tools/leanground.json", out)
        self.assertIn("  tools/b.py", out)
        code, out = self.run_upgrade("--apply")
        self.assertEqual(1, code)
        self.assertIn("adopt the kit first", out)

    def test_an_executable_kit_file_is_named_for_chmod(self):
        code, out = self.run_upgrade("--base", self.base)
        self.assertIn("git add --chmod=+x .githooks/commit-msg", out)


if __name__ == "__main__":
    unittest.main()
