"""Tests for tools/verify.py, the package gate. Run from the repository root:

    python -m unittest tools/test_verify.py
"""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify  # noqa: E402


def step(name, code=0, text="", sleep=0, **extra):
    """A step running this Python: prints text, sleeps, exits with code."""
    script = f"import sys, time; print({text or name!r}); time.sleep({sleep}); sys.exit({code})"
    return {"name": name, "command": [sys.executable, "-c", script], **extra}


class Verify(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.summary = self.repo / "working" / "verify" / "summary.md"

    def configure(self, steps, budget=0):
        path = self.repo / "tools" / "leanground.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"verify_steps": steps, "verify_max_minutes": budget}), encoding="utf-8")

    def run_verify(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = verify.main(list(args), self.repo)
        return code, out.getvalue()

    def test_all_pass(self):
        self.configure([step("build", text="built ok"), step("test")])
        code, out = self.run_verify()
        self.assertEqual(0, code)
        lines = out.splitlines()
        self.assertEqual(3, len(lines), out)
        self.assertRegex(lines[0], r"^build \.\.\. PASS \d+\.\ds$")
        self.assertNotIn("built ok", out)
        self.assertEqual("verify: PASSED, all 2 steps. Summary: working/verify/summary.md", lines[-1])
        summary = self.summary.read_text(encoding="utf-8")
        self.assertIn("# verify: PASSED, all 2 steps", summary)
        self.assertIn("| build | pass |", summary)
        self.assertIn("Slowest: ", summary)
        self.assertIn("built ok", (self.repo / "working" / "verify" / "1-build.log").read_text(encoding="utf-8"))

    def test_a_string_command_runs_in_the_shell(self):
        self.configure([{"name": "shell", "command": f'"{sys.executable}" -c "print(1)"'}])
        self.assertEqual(0, self.run_verify()[0])

    def test_a_failure_stops_and_names_the_steps_not_run(self):
        self.configure([step("build"), step("test", code=3, text="\n".join(f"line {n}" for n in range(50))),
                        step("lint"), step("docs")])
        code, out = self.run_verify()
        self.assertEqual(1, code)
        self.assertNotIn("lint ...", out)
        self.assertIn("verify: FAILED at test (exit 3); not run: lint, docs.", out.splitlines()[-1])
        summary = self.summary.read_text(encoding="utf-8")
        self.assertIn("| test | FAIL (exit 3) |", summary)
        self.assertIn("| lint | not run |", summary)
        self.assertIn("the last lines of working/verify/2-test.log", summary)
        self.assertIn("line 49", summary)
        self.assertNotIn("line 19\n", summary)
        self.assertIn("line 20\n", summary)

    def test_resume(self):
        marker = self.repo / "fixed"
        fails_until_fixed = {"name": "test", "command": [sys.executable, "-c",
                                                         f"import os, sys; sys.exit(0 if os.path.exists({str(marker)!r}) else 1)"]}
        self.configure([step("build", text="first build"), fails_until_fixed, step("lint")])
        self.assertEqual(1, self.run_verify()[0])
        marker.write_text("", encoding="utf-8")
        code, out = self.run_verify("--resume")
        self.assertEqual(0, code)
        self.assertNotIn("build ...", out)
        self.assertIn("test ... PASS", out)
        self.assertIn("lint ... PASS", out)
        summary = self.summary.read_text(encoding="utf-8")
        self.assertIn("| build | pass (earlier run) |", summary)
        self.assertIn("Resumed at test", summary)
        self.assertIn("first build", (self.repo / "working" / "verify" / "1-build.log").read_text(encoding="utf-8"))
        self.assertEqual(2, self.run_verify("--resume")[0])
        self.assertIn("nothing to resume", self.summary.read_text(encoding="utf-8"))

    def test_resume_refused_after_the_list_changed(self):
        self.configure([step("build"), step("test", code=1)])
        self.assertEqual(1, self.run_verify()[0])
        self.configure([step("build"), step("test", code=1), step("lint")])
        code, out = self.run_verify("--resume")
        self.assertEqual(2, code)
        self.assertIn("have changed", out)
        self.assertNotIn("build ...", out)

    def test_resume_with_no_earlier_run(self):
        self.configure([step("build")])
        code, out = self.run_verify("--resume")
        self.assertEqual(2, code)
        self.assertIn("no earlier run", out)

    def test_a_step_past_its_limit(self):
        self.configure([step("slow", sleep=20, max_minutes=0.02), step("after")])
        code, out = self.run_verify()
        self.assertEqual(1, code)
        self.assertIn("FAILED at slow (passed its limit of 0.02 min); not run: after", out)
        self.assertLess(float(out.split("FAIL ")[1].split("s")[0]), 15)

    def test_the_run_past_its_budget(self):
        self.configure([step("first", sleep=0.5), step("second", sleep=20), step("third")], budget=0.03)
        code, out = self.run_verify()
        self.assertEqual(1, code)
        self.assertIn("first ... PASS", out)
        self.assertIn("FAILED at second (passed the run's budget of 0.03 min); not run: third", out)

    def test_an_empty_step_list(self):
        self.configure([])
        code, out = self.run_verify()
        self.assertEqual(2, code)
        self.assertIn("has not set its verify steps", out)
        self.assertIn("REFUSED", self.summary.read_text(encoding="utf-8"))
        self.assertEqual(2, self.run_verify("--list")[0])

    def test_the_summary_is_overwritten_on_a_refused_run(self):
        self.configure([step("build")])
        self.assertEqual(0, self.run_verify()[0])
        self.assertIn("PASSED", self.summary.read_text(encoding="utf-8"))
        self.assertEqual(2, self.run_verify("--bogus")[0])
        summary = self.summary.read_text(encoding="utf-8")
        self.assertIn("REFUSED", summary)
        self.assertNotIn("PASSED", summary)
        self.assertEqual(0, self.run_verify()[0])
        self.configure([{"name": "no command"}])
        self.assertEqual(2, self.run_verify()[0])
        self.assertNotIn("PASSED", self.summary.read_text(encoding="utf-8"))

    def test_only_and_list(self):
        self.configure([step("build"), step("test", code=1), step("lint", max_minutes=2)])
        code, out = self.run_verify("--only", "lint")
        self.assertEqual(0, code)
        self.assertNotIn("build ...", out)
        self.assertIn("not the whole gate", self.summary.read_text(encoding="utf-8"))
        self.assertFalse((self.repo / "working" / "verify" / "state.json").exists())
        self.assertEqual(2, self.run_verify("--only", "nothing")[0])
        code, out = self.run_verify("--list")
        self.assertEqual(0, code)
        self.assertIn("3. lint: ", out)
        self.assertIn("(at most 2 min)", out)


if __name__ == "__main__":
    unittest.main()
