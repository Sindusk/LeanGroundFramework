"""Tests for tools/docs.py and tools/docs_sig.py. Run from the repository root:

    python -m unittest tools/test_docs.py
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

import docs  # noqa: E402
import docs_sig  # noqa: E402

DESIGN = """# Design

## 1. Vision

Intro.

### 1.1 Priorities

Priorities.

## 4. Systems

### 4.6 Search

Search.

```
## 4.7 not a heading inside a fence
```

#### 4.6.1 Built rules

The index.

### 4.60 Far away

Far.

### 4.7 Storage

Storage.

## 6. Roadmap

### 6.2 Open Design Questions

A new question takes the next free number: **20**.

#### Open questions

##### Search

- **7.** Which index should search use? Found cutting Search Filters.
  - **(a)** the first.
- **8.** A second question.

#### Idea backlog

##### A. Offline

A pitch.

### 6.4 Delivered

None yet.

### 6.7 Known Issues

None yet.

## 11. Open Tuning Questions

None yet.
"""

LEDGER = """# Ledger

One line per item.
The next package ID is TS-103.

## Work-Ready

- **Search Filters** — cut
  - TS-100 Facets (Claude Opus 5.5) — can be built
  - TS-101 Saved searches (Claude Sonnet 5.5) — waits on TS-100 and question 7
- TS-102 Lone fix (Claude Opus 5.5) — can be built

## Designed

None yet.

## Undesigned

- **Offline** — its design round

## Initiatives

### Search Filters

Filters on the search page (4.6).

- **TS-100 Facets.** *Outcome:* facets on 2026-10-01. *Touches:* 4.6.1, 4.7; `search/Index`.
- **TS-101 Saved searches.** *Outcome:* saved. *Depends on:* TS-100.

### Offline

Offline mode.

### Standalone Work Packages

- **TS-102 Lone fix.** *Outcome:* fixed (4.7).
"""

HISTORY = """# History

## Decision Log

| Date | Decision | Reason |
|---|---|---|
| 2026-10-01 | Search exists (4.6) | Because |
"""

ROUNDS = """# Design Questions

**A short glossary** for readers outside the project.

- **Facet:** a filter.

---

Consolidated rounds: none yet.
"""

ARCHIVE_INDEX = """# Documentation archive

## Index

None yet.
"""

WHERE = """# Where things live

## Systems

**Search** (4.6). Index: `search/Index`. Tests: `tests/test_index.py`.

**Storage** (4.7). Files: `storage/Files`, uses the search index.
"""

CONFIG = {"prefix": "TS", "owner": "Owner", "bootstrapped": True, "budgets": {"CLAUDE.md": 200},
          "source_roots": ["src"], "core": ["tools/docs.py"]}


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, encoding="utf-8", check=True).stdout


def run(function, *args, **kwargs):
    """(result, printed output) of a call."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = function(*args, **kwargs)
    return result, out.getvalue()


class Repo(unittest.TestCase):
    """A fixture repository with every document the tool reads, committed."""

    files = {}

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        docs._configs.clear()
        docs._plugins.clear()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "core.autocrlf", "false")
        base = {
            "DESIGN.md": DESIGN, "LEDGER.md": LEDGER, "design-history.md": HISTORY, "design-questions.md": ROUNDS,
            "docs/archive/README.md": ARCHIVE_INDEX, "docs/agent-notes/where-things-live.md": WHERE,
            "CLAUDE.md": "# Instructions\n\nRead `DESIGN.md` section 4.\n",
            "tools/leanground.json": json.dumps(CONFIG),
        }
        for name, text in {**base, **self.files}.items():
            self.put(name, text)
        self.commit("Start")

    def put(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        docs.write(path, text)

    def read(self, name):
        return (self.repo / name).read_text(encoding="utf-8")

    def commit(self, message):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", message)

    def configure(self, **changes):
        self.put("tools/leanground.json", json.dumps({**CONFIG, **changes}))
        docs._configs.clear()

    def problems(self):
        git(self.repo, "add", "-A")
        files = docs.tracked_markdown(self.repo)
        sources = [s for s in docs.source_files(self.repo) if not docs.is_core(self.repo, s)]
        return [detail for _, _, detail in docs.find_problems(self.repo, files, sources)[0]]

    def main(self, *args):
        git(self.repo, "add", "-A")
        return run(docs.main, list(args), self.repo)


class StoppingRule(unittest.TestCase):
    def setUp(self):
        self.design = docs.Doc("DESIGN.md", DESIGN)

    def block(self, number):
        return self.design.text(*docs.heading_block(self.design, docs.find_section(self.design, number)))

    def test_a_section_holds_its_numbered_subsections_but_not_a_longer_number(self):
        text = self.block("4.6")
        self.assertIn("The index.", text)
        self.assertNotIn("Far.", text)

    def test_a_heading_in_a_fence_is_not_a_heading(self):
        self.assertNotIn("4.7 not a heading", [h[2] for h in self.design.headings])

    def test_section_one_does_not_hold_section_eleven(self):
        self.assertNotIn("Open Tuning", self.block("1"))

    def test_own_block_stops_at_the_first_subheading(self):
        start, end = docs.own_block(self.design, docs.find_section(self.design, "4.6"))
        self.assertTrue(self.design.text(start, end).endswith("## 4.7 not a heading inside a fence\n```"))


class Questions(unittest.TestCase):
    def test_open_questions_run_through_their_sub_items(self):
        design = docs.Doc("DESIGN.md", DESIGN)
        spans = docs.open_questions(design)
        self.assertEqual([7, 8], sorted(spans))
        self.assertIn("(a)", design.text(*spans[7]))

    def test_cited_questions_reads_lists(self):
        self.assertEqual([7, 8, 9], docs.cited_questions("waits on questions 7, 8 and 9"))

    def test_question_asked_stops_at_the_question_mark(self):
        self.assertEqual("Which index should search use?",
                         docs.question_asked("- **7.** Which index should search use? Found cutting."))


class Citations(unittest.TestCase):
    def test_dates_versions_and_model_names_are_not_sections(self):
        text = "*Outcome:* on 2026-10-01 for v1.2 by Claude Opus 5.5. *Touches:* 4.6.1, 4.7; `x`. See section 11."
        self.assertEqual(["4.6.1", "4.7", "11"], docs.cited_sections(text))

    def test_prose_cites_design_and_section(self):
        self.assertEqual({"4.6", "11"}, docs.prose_sections("`DESIGN.md` 4.6 and section 11"))


class LedgerFormat(unittest.TestCase):
    def setUp(self):
        self.ledger = docs.Ledger(docs.Doc("LEDGER.md", LEDGER), docs.Ids("TS"))

    def test_items_packages_and_owners(self):
        self.assertEqual(["Search Filters", "Offline"], [i["name"] for i in self.ledger.items])
        owners = {p["id"]: p["owner"] for p in self.ledger.packages}
        self.assertEqual({"TS-100": "Search Filters", "TS-101": "Search Filters",
                          "TS-102": docs.STANDALONE_HEADING}, owners)
        self.assertEqual(103, self.ledger.next_id)

    def test_blocks_pair_with_lines(self):
        self.assertEqual(set(self.ledger.blocks), {"TS-100", "TS-101", "TS-102"})
        self.assertEqual("Search Filters", self.ledger.blocks["TS-101"]["initiative"])

    def test_a_placeholder_prefix_is_matched_literally(self):
        ids = docs.Ids("{{PREFIX}}")
        self.assertEqual("{{PREFIX}}-7", ids.parse("{{PREFIX}}-7"))
        self.assertEqual(["100"], ids.next_id.findall("The next package ID is {{PREFIX}}-100."))


class Check(Repo):
    def test_the_fixture_passes(self):
        self.assertEqual([], self.problems())

    def test_ledger_faults(self):
        self.put("LEDGER.md", LEDGER
                 .replace("- **Offline** — its design round", "- **Offline** — its design round\n| a | table |\n"
                          "- **Ghost** — see [here](x)")
                 .replace("TS-101 Saved searches (Claude Sonnet", "TS-101 Saved search (Claude Sonnet")
                 .replace("The next package ID is TS-103.", "The next package ID is TS-102.")
                 .replace("waits on TS-100 and question 7", "waits on TS-99 and question 99"))
        found = "\n".join(self.problems())
        for expected in ("table row", "holds a link", '"Ghost" has no block', 'block says "Saved searches"',
                         "is not above TS-102", "question 99 is named", 'waits on "TS-99"'):
            self.assertIn(expected, found)

    def test_a_non_ascii_filename_is_tracked(self):
        git(self.repo, "config", "core.quotepath", "true")  # git's default, which quotes the name in ls-files
        self.put("docs/café.md", "Cites section 99.\n")
        self.assertIn("docs/café.md", docs.tracked_markdown(self.repo))
        self.assertIn("cites section 99", "\n".join(self.problems()))

    def test_status_word_in_a_heading(self):
        self.put("LEDGER.md", LEDGER.replace("### Offline", "### Offline (designed)")
                 .replace("- **Offline** —", "- **Offline (designed)** —"))
        self.assertIn('carries the status word "designed"', "\n".join(self.problems()))

    def test_a_missing_section_and_document(self):
        self.put("CLAUDE.md", "# Instructions\n\nRead `DESIGN.md` 9.9 and `missing.md`.\n")
        found = "\n".join(self.problems())
        self.assertIn("cites section 9.9", found)
        self.assertIn("names missing.md", found)

    def test_a_source_file_citing_a_missing_section(self):
        self.put("src/search/Index.py", "# DESIGN 4.6.1 and DESIGN 5.5\n")
        self.put("tools/docs.py", "# DESIGN 9.9, an example in the kit's own code\n")
        self.assertEqual(["cites DESIGN 5.5, which DESIGN.md does not have"], self.problems())

    def test_a_gendered_pronoun(self):
        self.put("notes.md", "# Notes\n\nAsk her.\n\n```\nhe in code is fine\n```\n")
        self.assertEqual(['uses the gendered pronoun "her"; write they, them or the name'], self.problems())

    def test_placeholders_once_bootstrapped(self):
        self.put("notes.md", "# {{PROJECT}}\n\n<!-- bootstrap: fill this -->\n")
        self.put("LEANGROUND.md", "# Kit\n\n`{{PREFIX}}` is the prefix.\n")
        self.put(".claude/skills/kit/SKILL.md", "# Kit skill\n\nFills `{{PROJECT}}`.\n")
        self.configure(core=["tools/docs.py", ".claude/skills/kit/"], budgets={"CLAUDE.md": 200,
                                                                              ".claude/skills/kit/SKILL.md": 100})
        self.assertEqual(2, len([p for p in self.problems() if "still holds" in p]))
        self.configure(bootstrapped=False, core=["tools/docs.py", ".claude/skills/kit/"],
                       budgets={"CLAUDE.md": 200, ".claude/skills/kit/SKILL.md": 100})
        self.assertEqual([], self.problems())

    def test_a_package_being_built_needs_its_history_row(self):
        self.put("LEDGER.md", LEDGER.replace("TS-100 Facets (Claude Opus 5.5) — can be built",
                                             "TS-100 Facets (Claude Opus 5.5) — being built"))
        self.assertIn("has no row for it", "\n".join(self.problems()))
        self.put("design-history.md", HISTORY + "| 2026-10-02 | TS-100 Facets's rules (4.6.1) | Why |\n")
        self.assertEqual([], self.problems())

    def test_an_example_naming_a_closed_package(self):
        self.put("notes.md", "# Notes\n\nRun `python tools/docs.py TS-050`.\n")
        self.assertIn("gives TS-050 as an example", "\n".join(self.problems()))

    def test_a_stale_table_of_contents(self):
        self.put("notes.md", "# Notes\n\n## Contents\n\n- [One](#one)\n\n## One\n\n## Two\n")
        self.assertIn("at entry 2 it should read - [Two](#two)", "\n".join(self.problems()))

    def test_a_reused_question_number(self):
        self.put("docs/initiatives/search.md", "# Search\n\n## Open questions\n\n- **7.** Again.\n")
        self.assertIn("asks question 7, which DESIGN.md", "\n".join(self.problems()))

    def test_a_decision_stub_left(self):
        self.put("DESIGN.md", DESIGN.replace("- **8.** A second question.",
                                             "- **8.** A second question.\n" + docs.decision_stub("2026-10-02", "b", "Owner")))
        self.assertIn("still holds record's TODO", "\n".join(self.problems()))

    def test_a_block_naming_a_closed_question(self):
        self.put("LEDGER.md", LEDGER.replace("*Outcome:* saved.", "*Outcome:* saved, as question 99 decided."))
        self.assertIn("a block names question 99", "\n".join(self.problems()))

    def test_new_files_count_before_their_first_commit(self):
        self.put("notes.md", "# Notes\n\nSee `missing.md`.\n")
        files = docs.tracked_markdown(self.repo)
        self.assertIn("notes.md", files)
        self.put(".gitignore", "ignored.md\n")
        self.put("ignored.md", "# Ignored\n")
        self.assertNotIn("ignored.md", docs.tracked_markdown(self.repo))

    def test_outside_a_repository(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        with self.assertRaises(SystemExit) as raised:
            docs.tracked(outside)
        self.assertIn("git init", str(raised.exception))

    def test_a_project_check(self):
        self.put("tools/project_docs.py", "def problems(repo, files):\n    return [('x.md', 1, 'project rule')]\n")
        self.assertEqual(["project rule"], self.problems())


class Budgets(Repo):
    def test_over_budget_and_unbudgeted(self):
        self.put("CLAUDE.md", "# Instructions\n\n" + "word " * 200 + "\n")
        self.put(".claude/skills/demo/SKILL.md", "---\nname: demo\ndescription: " + "long " * 120 + "\n---\n\nBody.\n")
        self.put(".claude/skills/demo/why.md", "# Why\n\nNever loaded to follow a step.\n")
        found = "\n".join(self.problems())
        self.assertIn("over its budget of 200", found)
        self.assertIn("has no token budget", found)
        self.assertIn("its description is", found)
        self.assertNotIn("why.md", found)

    def test_a_sentence_two_loaded_files_repeat(self):
        sentence = "Every behaviour change gets a dated row in the design history before anyone commits it."
        self.put("CLAUDE.md", f"# Instructions\n\n{sentence}\n")
        self.put("AGENTS.md", f"# Agents\n\n{sentence}\n")
        self.configure(budgets={"CLAUDE.md": 200, "AGENTS.md": 200})
        self.assertIn("repeats a sentence of", "\n".join(self.problems()))

    def test_two_agents_never_share_a_context(self):
        sentence = "Do not commit, stage or push anything, and never spawn a subagent of your own."
        self.put(".claude/agents/one.md", f"# One\n\n{sentence}\n")
        self.put(".claude/agents/two.md", f"# Two\n\n{sentence}\n")
        self.configure(budgets={"CLAUDE.md": 200, ".claude/agents/one.md": 100, ".claude/agents/two.md": 100})
        self.assertEqual([], self.problems())
        self.put("CLAUDE.md", f"# Instructions\n\n{sentence}\n")
        self.assertIn("repeats a sentence of", "\n".join(self.problems()))


class Reading(Repo):
    def test_a_package_with_its_menu(self):
        code, out = self.main("ts-100")
        self.assertEqual(0, code)
        self.assertIn("- **TS-100 Facets.**", out)
        self.assertNotIn("- **TS-101", out)
        self.assertIn("Left out, the Initiative's other packages: Saved searches (TS-101)", out)
        self.assertIn("4.6.1    Built rules", out)
        self.assertNotIn("2026", out.split("== Design sections")[1])

    def test_a_package_names_its_questions_and_packages(self):
        _, out = self.main("TS-101")
        self.assertIn("- **7.** Which index", out)
        self.assertIn("TS-100   Facets: on the ledger, can be built", out)

    def test_a_standalone_package(self):
        code, out = self.main("TS-102")
        self.assertEqual(0, code)
        self.assertIn("- TS-102 Lone fix", out)

    def test_sections_with_options(self):
        _, out = self.main("4.6", "--own", "4.7", "--grep", "stor")
        self.assertIn("4.6 Search, without its subsections", out)
        self.assertIn("4.6.1    Built rules", out)
        self.assertIn("4.7 Storage: lines matching stor", out)
        self.assertIn("Note: --grep filters only the section before it, so 4.6 printed whole.", out)

    def test_a_question_an_initiative_and_a_heading(self):
        self.assertIn("**(a)** the first", self.main("q7")[1])
        self.assertIn("Offline mode.", self.main("Offline")[1])
        self.assertIn("**Search** (4.6)", self.main("where-things-live.md", "Systems")[1])

    def test_where_by_name_and_by_mention(self):
        self.assertIn("**Search** (4.6)", self.main("where", "search")[1])
        _, out = self.main("where", "Files")
        self.assertIn("these paragraphs mention it", out)
        self.assertIn("**Storage**", out)

    def test_the_ledger_alone(self):
        _, out = self.main("ledger")
        self.assertIn("- **Offline** — its design round", out)
        self.assertNotIn("Offline mode.", out)

    def test_toc_outline_and_tail(self):
        self.assertIn("- [1. Vision](#1-vision)", self.main("toc", "DESIGN.md")[1])
        self.assertIn("4.6 Search", self.main("DESIGN.md")[1])
        self.assertIn("2026-10-01", self.main("tail", "design-history.md", "1")[1])

    def test_grep_cuts_long_lines(self):
        doc = docs.Doc("x.md", "a" * 200 + "MATCH" + "b" * 200)
        line = docs.grep_block(doc, 1, 1, "match")[0][1]
        self.assertEqual("…" + "a" * 80 + "MATCH" + "b" * 80 + "…", line)

    def test_help_for_one_command(self):
        _, out = self.main("help", "status")
        self.assertTrue(out.startswith("    python tools/docs.py status"))

    def test_an_unknown_request(self):
        code, out = self.main("nothing here")
        self.assertEqual(1, code)
        self.assertIn("Initiatives: Search Filters, Offline, Standalone Work Packages", out)


class ProjectCommands(Repo):
    files = {"tools/project_docs.py": (
        "def hello(repo, args):\n    print('hello', *args)\n    return 0\n\n"
        "COMMANDS = {'hello': (hello, '    python tools/docs.py hello NAME              greets NAME')}\n")}

    def test_a_project_command_runs_and_has_help(self):
        self.assertEqual((0, "hello world\n"), self.main("hello", "world"))
        self.assertIn("greets NAME", self.main("help", "hello")[1])
        self.assertIn("This project's own commands", self.main("help")[1])


class Status(Repo):
    def test_status_writes_the_line(self):
        self.put("design-history.md", HISTORY + "| 2026-10-02 | TS-100 Facets's rules (4.6.1) | Why |\n")
        code, out = self.main("status", "TS-100", "being", "built")
        self.assertEqual(0, code, out)
        self.assertIn("  - TS-100 Facets (Claude Opus 5.5) — being built", self.read("LEDGER.md"))

    def test_status_of_an_unknown_package(self):
        self.assertEqual(1, self.main("status", "TS-999", "x")[0])

    def test_a_status_that_would_fail_the_check_writes_nothing(self):
        before = self.read("LEDGER.md")
        for status in (["waits", "on", "question", "99"], ["being", "built"], ["waits", "on", "TS-99"]):
            code, out = self.main("status", "TS-100", *status)
            self.assertEqual(1, code, out)
            self.assertIn("not written", out)
            self.assertEqual(before, self.read("LEDGER.md"))
        # a fault on another line is the check's to report, not a reason to refuse this one
        self.put("LEDGER.md", before.replace("The next package ID is TS-103.", "The next package ID is TS-102."))
        self.main("status", "TS-100", "waits", "on", "question", "8")
        self.assertIn("TS-100 Facets (Claude Opus 5.5) — waits on question 8", self.read("LEDGER.md"))


class Close(Repo):
    def build_package(self):
        self.put("src/search/Index.py", "def facets():\n    return []\n")
        self.commit("TS-100 Facets: start building; the rules")
        self.put("tests/test_index.py", "def test_facets_count():\n    assert True\n")
        self.put("src/search/Index.py", "def facets():\n    return [1]\n")
        self.commit("TS-100 Facets: count facets")
        self.configure(source_roots=["src", "tests"])

    def test_close_a_package(self):
        self.build_package()
        code, out = self.main("close", "TS-100", "--steps", "4", "--date", "2026-10-05")
        self.assertIn("Created docs/archive/initiatives/2026-10-05-search-filters-record.md", out)
        ledger = self.read("LEDGER.md")
        self.assertNotIn("TS-100 Facets", ledger)
        self.assertIn("TS-101 Saved searches (Claude Sonnet 5.5) — waits on question 7", ledger)
        record = self.read("docs/archive/initiatives/2026-10-05-search-filters-record.md")
        self.assertIn("> - **TS-100 Facets.**", record)
        self.assertIn("`src/search/Index.py`", record)
        self.assertIn("`tests/test_index.py` (facets count)", record)
        self.assertIn("Its commits: count facets.", record)
        self.assertIn("all 4 steps passed", record)
        self.assertIn("- `initiatives/2026-10-05-search-filters-record.md`: Search Filters, open, one block per"
                      " package; TS-100 Facets (2026-10-05).", self.read("docs/archive/README.md"))
        self.assertNotIn("None yet.", self.read("docs/archive/README.md"))
        self.assertIn("| 2026-10-05 | TS-100 approved", self.read("design-history.md"))
        self.assertEqual(0, code, out)

    def test_close_lists_only_the_packages_own_commits_files(self):
        self.put("src/search/Index.py", "def facets():\n    return []\n")
        self.commit("TS-100 Facets: start building; the rules")
        self.put("src/storage/Files.py", "def save():\n    pass\n")
        self.put("tests/test_files.py", "def test_saves():\n    assert True\n")
        self.commit("Storage: save files\n\nNot TS-100's work, though made over its dates.")
        self.put("tests/test_index.py", "def test_facets_count():\n    assert True\n")
        self.put("src/search/Index.py", "def facets():\n    return [1]\n")
        self.commit("TS-100 Facets: count facets")
        self.put("tests/test_index.py", "def test_facets_count():\n    assert 1\n\n\ndef test_facets_sort():\n    pass\n")
        self.commit("TS-100 Facets: sort facets")
        self.put("src/search/Later.py", "def later():\n    pass\n")
        self.commit("After the package")
        self.configure(source_roots=["src", "tests"])
        self.main("close", "TS-100", "--date", "2026-10-05")
        record = self.read("docs/archive/initiatives/2026-10-05-search-filters-record.md")
        self.assertIn("(these changed: `src/search/Index.py`)", record)
        self.assertIn("- Tests: `tests/test_index.py` (facets count; facets sort).", record)
        for other in ("Files.py", "test_files.py", "Later.py"):
            self.assertNotIn(other, record)

    def test_close_drops_the_id_from_the_middle_of_a_wait_list_and_says_so(self):
        self.put("LEDGER.md", LEDGER.replace("— waits on TS-100 and question 7",
                                             "— waits on question 7 and TS-100 and TS-102"))
        self.commit("A three-part wait")
        code, out = self.main("close", "TS-100", "--date", "2026-10-05")
        self.assertIn("TS-101 Saved searches (Claude Sonnet 5.5) — waits on question 7 and TS-102",
                      self.read("LEDGER.md"))
        self.assertIn("TS-101 now reads: waits on question 7 and TS-102", out)
        self.assertNotIn("standing still names TS-100", out)

    def test_close_rewrites_bare_mentions_when_delivered(self):
        self.main("close", "TS-100", "--date", "2026-10-05", "--delivered", "the delivered facets (4.6.1)")
        self.assertIn("*Depends on:* the delivered facets (4.6.1).", self.read("LEDGER.md"))

    def test_close_a_standalone_package(self):
        self.main("close", "TS-102", "--date", "2026-10-05")
        record = self.read("docs/archive/initiatives/2026-10-05-lone-fix-record.md")
        self.assertIn("A standalone Work Package", record)
        self.assertIn("Manual check: none", record)

    def test_close_an_initiative(self):
        code, out = self.main("close-initiative", "Search Filters")
        self.assertEqual(1, code)
        self.assertIn("still has TS-100 and TS-101 on the ledger", out)
        self.main("close", "TS-100", "--date", "2026-10-05")
        self.main("close", "TS-101", "--date", "2026-10-06")
        code, out = self.main("close-initiative", "Search Filters", "--date", "2026-10-07")
        self.assertNotIn("### Search Filters", self.read("LEDGER.md"))
        design = self.read("DESIGN.md")
        self.assertIn("**Search Filters** (2026-10-05 to 2026-10-07): TODO: what a user now has. Packages TS-100 and"
                      " TS-101.", design)
        self.assertNotIn("### 6.4 Delivered\n\nNone yet.", design)
        record = self.read("docs/archive/initiatives/2026-10-05-search-filters-record.md")
        self.assertIn("Delivered and closed on 2026-10-07 by owner approval, after TS-101. Two packages", record)
        self.assertIn("closed 2026-10-07, one block per package", self.read("docs/archive/README.md"))

    def test_closing_an_initiative_removes_its_working_document_line(self):
        # The ledger writes the working document's path bare under the Initiative's line, before its packages.
        self.put("LEDGER.md", self.read("LEDGER.md").replace(
            "- **Search Filters** — cut\n", "- **Search Filters** — cut\n  docs/initiatives/search.md\n"))
        self.main("close", "TS-100", "--date", "2026-10-05")
        self.main("close", "TS-101", "--date", "2026-10-06")
        self.assertIn("  docs/initiatives/search.md\n", self.read("LEDGER.md"))
        code, out = self.main("close-initiative", "Search Filters", "--date", "2026-10-07")
        self.assertEqual(0, code, out)
        self.assertNotIn("docs/initiatives/search.md", self.read("LEDGER.md"))
        self.assertIn("Its working document docs/initiatives/search.md: move it unedited", out)

    def test_id_ranges(self):
        self.assertEqual("TS-1 to TS-3 and TS-7", docs.id_ranges(["TS-2", "TS-1", "TS-3", "TS-7"], docs.Ids("TS")))


class Drafts(Repo):
    DRAFT = """## Questions: DESIGN.md Storage

Storage questions.

- **G1.** Where do files go? See G2.
- **G2.** How big? Holds TS-101.

## Round 1 (2026-10-02): storage

### Files

#### QG2. How big?

**Recommendation:** (a). Cost of being wrong: low.

> **Response:**

#### QG1. Where?

> **Response:**

## Glossary

- **Facet:** already there.
- **Shard:** a piece.
"""

    def test_round_add_numbers_raises_and_merges(self):
        self.put("draft.md", self.DRAFT)
        code, out = self.main("round", "add", str(self.repo / "draft.md"))
        self.assertEqual(0, code, out)
        design = self.read("DESIGN.md")
        self.assertIn("##### Storage\n\nStorage questions.\n\n- **20.** How big? Holds TS-101.\n- **21.** Where do files"
                      " go? See question 20.", design)
        self.assertIn("next free number: **22**", design)
        rounds = self.read("design-questions.md")
        self.assertIn("#### Q20. How big?", rounds)
        self.assertIn("- **Shard:** a piece.", rounds)
        self.assertEqual(1, rounds.count("**Facet:**"))
        self.assertIn("**Recommendation:** (a).", self.main("round")[1])
        self.assertNotIn("Cost of being wrong", self.main("round")[1])

    def test_record_answers(self):
        self.put("draft.md", self.DRAFT)
        self.main("round", "add", str(self.repo / "draft.md"))
        code, out = self.main("record", "20=rec", "21=(b), because", "--date", "2026-10-03")
        design = self.read("DESIGN.md")
        self.assertIn("> **Decision (2026-10-03, Owner):** Accepts the recommendation.", design)
        self.assertIn('The response: "(b), because"', design)
        self.assertNotIn("#### Q2", self.read("design-questions.md"))
        self.assertNotIn("### Files", self.read("design-questions.md"))
        self.assertEqual(1, code)  # the stub's TODO is still to write
        self.assertIn("still holds record's TODO", out)

    def test_a_round_of_questions_already_raised(self):
        self.put("draft.md", "## Round 1 (2026-10-02): search\n\n#### Q7. Which index?\n\n> **Response:**\n\n"
                             "#### Q8. Second?\n\n> **Response:**\n")
        code, out = self.main("round", "add", str(self.repo / "draft.md"))
        self.assertEqual(0, code, out)
        self.assertIn("#### Q7. Which index?", self.read("design-questions.md"))
        self.assertIn("next free number: **20**", self.read("DESIGN.md"))
        self.put("draft.md", "## Round 2 (2026-10-03): x\n\n#### Q50. Gone?\n\n> **Response:**\n")
        self.assertEqual(1, self.main("round", "add", str(self.repo / "draft.md"))[0])

    def test_an_answered_round_is_removed_and_listed(self):
        self.put("design-questions.md", ROUNDS.replace("Consolidated rounds: none yet.", "Answered rounds: none yet."))
        self.put("draft.md", "## Round 1 (2026-10-02): search\n\n### Index\n\n#### Q7. Which index?\n\n> **Response:**\n")
        self.main("round", "add", str(self.repo / "draft.md"))
        self.put("LEDGER.md", LEDGER.replace(" and question 7", ""))
        self.main("record", "7=rec", "--date", "2026-10-03")
        rounds = self.read("design-questions.md")
        self.assertNotIn("## Round 1", rounds)
        self.assertIn("Answered rounds: Round 1 (2026-10-02).", rounds)

    def test_two_questions_parts_are_refused(self):
        self.put("draft.md", "## Questions: DESIGN.md A\n\n- **G1.** a?\n\n## Questions: DESIGN.md B\n\n- **G2.** b?\n")
        code, out = self.main("raise", str(self.repo / "draft.md"))
        self.assertEqual(1, code)
        self.assertIn("two `## Questions:` parts", out)

    def test_raise_into_an_empty_open_questions(self):
        self.put("DESIGN.md", DESIGN.replace("##### Search\n\n- **7.** Which index should search use? Found cutting"
                                             " Search Filters.\n  - **(a)** the first.\n- **8.** A second question.",
                                             "None yet."))
        self.put("LEDGER.md", LEDGER.replace(" and question 7", ""))
        self.put("draft.md", "## Questions: DESIGN.md Search\n\n- **G1.** First?\n")
        code, out = self.main("raise", str(self.repo / "draft.md"))
        self.assertEqual(0, code, out)
        self.assertIn("#### Open questions\n\n##### Search\n\n- **20.** First?\n\n#### Idea backlog", self.read("DESIGN.md"))

    def test_a_bad_draft_writes_nothing(self):
        self.put("draft.md", "## Questions: DESIGN.md Search\n\n- **No id.** First?\n")
        before = self.read("DESIGN.md")
        self.assertEqual(1, self.main("raise", str(self.repo / "draft.md"))[0])
        self.assertEqual(before, self.read("DESIGN.md"))

    def test_drop_questions_and_a_heading(self):
        self.put("LEDGER.md", LEDGER.replace(" and question 7", ""))
        code, out = self.main("drop", "q7")
        self.assertNotIn("- **7.**", self.read("DESIGN.md"))
        self.assertEqual(0, code, out)
        self.main("drop", "q8")
        _, out = self.main("decisions", "--all")
        self.assertIn("No open question has a decision written.", out)
        self.main("drop", "DESIGN.md", "A. Offline")
        self.assertNotIn("A pitch.", self.read("DESIGN.md"))

    def test_decisions_brief(self):
        self.put("DESIGN.md", DESIGN.replace("  - **(a)** the first.",
                                             "  - **(a)** the first.\n  > **Decision (2026-10-02, Owner):** (a)."))
        _, out = self.main("decisions", "q7")
        self.assertIn("q7  Which index should search use?", out)
        self.assertIn("> **Decision (2026-10-02, Owner):** (a).", out)


class HistoryAndPackages(Repo):
    def test_history_rows_are_validated(self):
        rows = ["| 2026-02-30 | x (4.6) | y |", "| 2026-10-02 | no cite | y |", "| 2026-10-02 | x (4.6) | ask him |",
                "| 2026-10-02 | x (4.6) |"]
        details = [detail for _, detail in docs.history_problems(rows)]
        self.assertEqual(4, len(details))
        self.put("rows.md", "| 2026-10-02 | Facets counted (4.6.1) | Asked for |\n")
        code, _ = self.main("history", "add", str(self.repo / "rows.md"))
        self.assertEqual(0, code)
        self.assertTrue(self.read("design-history.md").rstrip().endswith("| Asked for |"))

    def test_insert_and_replace_a_package(self):
        self.put("pkg.md", "  - TS-110 Export (Claude Opus 5.5) — can be built\n"
                           "- **TS-110 Export.** *Outcome:* export.\n")
        code, out = self.main("ledger", "insert", str(self.repo / "pkg.md"), "--after", "TS-100")
        self.assertEqual(0, code, out)
        ledger = self.read("LEDGER.md")
        self.assertIn("The next package ID is TS-111.", ledger)
        self.assertIn("- **TS-100 Facets.**", ledger.split("- **TS-110 Export.**")[0])
        self.put("pkg.md", "- **TS-110 Export.** *Outcome:* export as CSV.\n")
        self.main("ledger", "replace", "TS-110", str(self.repo / "pkg.md"))
        self.assertIn("export as CSV", self.read("LEDGER.md"))
        self.assertEqual(1, self.main("ledger", "insert", str(self.repo / "pkg.md"), "--after", "TS-100")[0])


class Waits(unittest.TestCase):
    def test_drop_wait(self):
        self.assertEqual("waits on XX-2", docs.drop_wait("waits on XX-1 and XX-2", "XX-1"))
        self.assertEqual("waits on questions 1 and 2, XX-3 and XX-4",
                         docs.drop_wait("waits on questions 1 and 2, XX-1, XX-3 and XX-4", "XX-1"))
        self.assertEqual("can be built", docs.drop_wait("waits on XX-1", "XX-1"))

    def test_drop_wait_takes_the_id_from_any_place(self):
        middle = "waits on question 26 and XX-100 and XX-101"
        self.assertEqual("waits on XX-100 and XX-101", docs.drop_wait(middle.replace("question 26 and ", "XX-99 and "),
                                                                    "XX-99"))  # first
        self.assertEqual("waits on question 26 and XX-101", docs.drop_wait(middle, "XX-100"))  # middle
        self.assertEqual("waits on question 26 and XX-100", docs.drop_wait(middle, "XX-101"))  # last
        self.assertEqual("waits on XX-1 and XX-3", docs.drop_wait("waits on XX-1, XX-2 and XX-3", "XX-2"))
        self.assertEqual("waits on XX-1 and XX-2", docs.drop_wait("waits on XX-1, XX-2 and XX-3", "XX-3"))
        self.assertEqual("can be built", docs.drop_wait("waits on XX-100", "XX-100"))  # only
        self.assertEqual("waits on XX-1000", docs.drop_wait("waits on XX-1000", "XX-100"))  # never a longer id
        self.assertEqual("no open questions; waits on question 26 and XX-101",
                         docs.drop_waits("no open questions; waits on question 26 and XX-100 and XX-101", "XX-100"))

    def test_wait_targets_leave_questions_out(self):
        self.assertEqual(["XX-1", "Offline"], docs.wait_targets("cut; waits on question 3, XX-1 and Offline"))
        self.assertEqual(["XX-1", "XX-2"], docs.wait_targets("waits on question 26 and XX-1 and XX-2"))
        self.assertEqual(["questions 1 and 2", "XX-1"], docs.wait_items("questions 1 and 2, XX-1"))


class Context(unittest.TestCase):
    def test_context_use_counts_each_response_once(self):
        line = json.dumps({"type": "assistant", "message": {"id": "m1", "usage": {
            "input_tokens": 10, "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 5}}})
        later = json.dumps({"type": "assistant", "message": {"id": "m2", "usage": {"input_tokens": 500}}})
        self.assertEqual((2, 1015, 500, 1015), docs.context_use([line, line, later, "not json"]))
        self.assertEqual((0, 0, 0, 0), docs.context_use(["not json"]))

    def test_the_ceiling_line_says_what_to_do_past_it(self):
        self.assertIn("within the 200k ceiling (handoff_past)", docs.ceiling_line(150_000, 200_000))
        past = docs.ceiling_line(210_000, 200_000)
        self.assertIn("past the 200k ceiling (handoff_past)", past)
        self.assertIn("paste-ready prompt for a new session", past)

    def test_context_reads_the_newest_transcript(self):
        home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        repo = home / "repo"
        repo.mkdir()
        original = Path.home
        Path.home = classmethod(lambda cls: home)
        self.addCleanup(setattr, Path, "home", original)
        folder = docs.transcript_dir(repo)
        folder.mkdir(parents=True)
        usage = [json.dumps({"type": "assistant", "message": {"id": f"m{n}", "usage": {"input_tokens": size}}})
                 for n, size in enumerate((30_000, 250_000, 240_000))]
        (folder / "abcdef12-session.jsonl").write_text("\n".join(usage), encoding="utf-8")
        docs._configs.clear()
        self.addCleanup(docs._configs.clear)
        code, out = run(docs.show_context, repo)
        self.assertEqual(0, code)
        self.assertIn("240k of context at the last request, peak 250k, 3 requests", out)
        self.assertIn("first request 30k", out)
        self.assertIn("past the 200k ceiling", out)


class SectionCap(Repo):
    files = {"DESIGN.md": DESIGN.replace("The index.\n", "The index.\n\n" + "word " * 3000 + "\n")}

    def test_a_section_over_the_cap_prints_its_own_text_and_menu(self):
        doc = docs.Doc("DESIGN.md", "## 4. A\n\nOwn text.\n\n### 4.1 B\n\n" + "word " * 5000 + "\n\n### 4.2 C\n\nShort.\n")
        _, out = run(docs.show_section, doc, docs.find_section(doc, "4"), False, None)
        self.assertIn("over section_cap (5,000)", out)
        self.assertIn("python tools/docs.py 4.1", out)
        self.assertIn("Own text.", out)
        self.assertIn("4.2      C", out)
        self.assertNotIn("word word", out)
        _, out = run(docs.show_section, doc, docs.find_section(doc, "4.2"), False, None)
        self.assertIn("Short.", out)
        self.assertNotIn("section_cap", out)

    def test_a_long_section_without_subsections_prints_whole(self):
        doc = docs.Doc("DESIGN.md", "## 4. A\n\n" + "word " * 5000 + "\n")
        _, out = run(docs.show_section, doc, docs.find_section(doc, "4"), False, None)
        self.assertIn("word word", out)

    def test_the_cap_comes_from_the_settings(self):
        _, out = self.main("4.6")
        self.assertIn("word word", out)
        self.configure(section_cap=1000)
        _, out = self.main("4.6")
        self.assertIn("over section_cap (1,000)", out)
        self.assertNotIn("word word", out)
        self.assertIn("4.6.1    Built rules", out)


LESSONS = "# Lessons waiting for a retro\n\nA header that must survive.\n"


class Lessons(Repo):
    files = {"docs/agent-notes/lessons.md": LESSONS}

    def test_lesson_add_appends_one_line(self):
        code, out = self.main("lesson", "add", "TS-100: three reruns → read the report first")
        self.assertEqual(0, code)
        self.assertIn("1 lesson waits for a retro", out)
        code, out = self.main("lesson", "add", "- TS-100: a second")
        self.assertIn("2 lessons wait", out)
        self.assertEqual(LESSONS + "\n- TS-100: three reruns → read the report first\n- TS-100: a second\n",
                         self.read("docs/agent-notes/lessons.md"))

    def test_lesson_add_refuses_an_empty_line_and_a_missing_file(self):
        self.assertEqual(1, self.main("lesson", "add", "  ")[0])
        (self.repo / "docs/agent-notes/lessons.md").unlink()
        code, out = self.main("lesson", "add", "x")
        self.assertEqual(1, code)
        self.assertIn("never creates it", out)
        self.assertFalse((self.repo / "docs/agent-notes/lessons.md").exists())

    def test_check_notes_a_due_retro_without_failing(self):
        self.configure(retro_after_lessons=2)
        for n in range(2):
            self.main("lesson", "add", f"lesson {n}")
        code, out = self.main("check")
        self.assertEqual(0, code)
        self.assertNotIn("a retro is due", out)
        self.main("lesson", "add", "lesson 3")
        code, out = self.main("check")
        self.assertEqual(0, code)
        self.assertIn("3 lessons wait in docs/agent-notes/lessons.md; a retro is due", out)


REPORT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="search" tests="3">
    <testcase classname="search.IndexTest" name="finds_a_word" file="tests/test_index.py"/>
    <testcase classname="search.IndexTest" name="ranks_by_score">
      <failure message="expected 2 but was 3">Traceback line one
line two</failure>
    </testcase>
    <testcase classname="search.CacheTest" name="expires"><error>Timeout after 5s
stack</error></testcase>
    <testcase classname="search.CacheTest" name="skipped"><skipped/></testcase>
  </testsuite>
</testsuites>
"""


class Failures(Repo):
    def test_no_setting_and_no_report(self):
        code, out = self.main("failures")
        self.assertEqual(1, code)
        self.assertIn("has not set test_report", out)
        self.configure(test_report="build/reports/*.xml")
        code, out = self.main("failures")
        self.assertEqual(1, code)
        self.assertIn("No test report at build/reports/*.xml", out)

    def test_a_report_with_no_failures(self):
        self.put("build/report.xml", REPORT.split("<testcase classname=\"search.IndexTest\" name=\"ranks")[0]
                 + "</testsuite></testsuites>\n")
        self.configure(test_report="build/report.xml")
        code, out = self.main("failures")
        self.assertEqual(0, code)
        self.assertIn("No failures: 1 tests in 1 report file", out)

    def test_failures_short_and_full(self):
        self.put("build/reports/TEST-search.xml", REPORT)
        self.configure(test_report="build/reports")
        code, out = self.main("failures")
        self.assertEqual(1, code)
        self.assertIn("2 failed of 4 tests", out)
        self.assertIn("ranks_by_score  (search.IndexTest)  expected 2 but was 3", out)
        self.assertIn("expires  (search.CacheTest)  Timeout after 5s", out)
        self.assertNotIn("Traceback", out)
        self.assertNotIn("finds_a_word", out)
        _, out = self.main("failures", "--full")
        self.assertIn("    Traceback line one\n    line two", out)
        self.assertIn("    stack", out)

    def test_an_unreadable_report(self):
        self.put("build/report.xml", "<testsuite><testcase")
        self.configure(test_report="build/*.xml")
        code, out = self.main("failures")
        self.assertEqual(1, code)
        self.assertIn("Could not read", out)


class NamedCommands(Repo):
    def skill(self, text):
        self.put(".claude/skills/demo/SKILL.md", text)
        self.configure(budgets={"CLAUDE.md": 200, ".claude/skills/demo/SKILL.md": 500})
        return [p for p in self.problems() if "python tools/docs.py" in p]

    def test_real_commands_and_lookups_pass(self):
        self.assertEqual([], self.skill(
            "# Demo\n\nRun `python tools/docs.py check`, `python tools/docs.py 4.6 --own`, `python tools/docs.py q7`,"
            " `python tools/docs.py TS-100`, `python tools/docs.py XX-nnn`, `python tools/docs.py \"Search Filters\"`,"
            " `python tools/docs.py <section>`, `python tools/docs.py DESIGN.md --grep x`, `python tools/docs.py"
            " lesson add \"<line>\"`, `python tools/docs.py history add <file>`, `python tools/docs.py failures`.\n"
            "\n```\npython tools/docs.py ledger insert pkg.md --after TS-100\n```\n"))

    def test_a_command_that_does_not_exist(self):
        found = self.skill("# Demo\n\nRead `python tools/docs.py testfail` and `python tools/docs.py lesson`.\n")
        self.assertEqual(2, len(found))
        self.assertIn("names `python tools/docs.py testfail`, which is no command", found[0])
        self.assertIn("where lesson needs add", found[1])

    def test_a_project_command_counts(self):
        self.put("tools/project_docs.py", "COMMANDS = {'hello': (None, '    python tools/docs.py hello')}\n")
        self.assertEqual([], self.skill("# Demo\n\n`python tools/docs.py hello`\n"))

    def test_every_usage_line_names_a_known_command(self):
        firsts = {line.split()[2] for line in docs.__doc__.splitlines() if line.startswith("    python tools/docs.py")}
        lookups = {word for word in firsts if docs.is_lookup(word)}
        self.assertEqual(set(), firsts - lookups - set(docs.DOCS_COMMANDS))
        self.assertLessEqual({"lesson", "failures"}, firsts)
        _, out = run(docs.main, ["help"])
        self.assertIn('python tools/docs.py lesson add "<line>"', out)
        self.assertIn("python tools/docs.py failures [--full]", out)


JAVA = """package demo;

/** A search index. Holds entries. */
public class SearchIndex {
    /** How many to keep. */
    public static final int LIMIT = 10;
    private int count;

    public SearchIndex(int count) {
        this.count = count;
    }

    /**
     * Rebuilds it.
     * @param all everything
     */
    public void rebuild(boolean all) {
        if (all) {
            count = 0;
        }
    }

    private void hidden() {}

    public enum Kind {
        ONE, TWO
    }
}
"""

PYTHON = '''"""A module."""

LIMIT = 10
_SECRET = 1
lower = 2


class Index(Base):
    """An index. Of things."""

    size: int = 0

    def __init__(self, size):
        self.size = size

    @staticmethod
    def build(items, *, fast=False) -> "Index":
        """Builds one."""
        return Index(len(items))

    def _private(self):
        pass


def _helper():
    pass
'''

TYPESCRIPT = """import { x } from "./x";

/** Options for a search. */
export interface SearchOptions {
  query: string;
  limit?: number;
}

export type Mode = "fast" | "slow";

/** Runs a search. Quickly. */
export async function search(options: SearchOptions): Promise<string[]> {
  const inner = { a: 1 };
  return [];
}

export const rank = (items: string[]): number => {
  return items.length;
};

function internal() {}

export class Searcher {
  private cache = new Map<string, string>();
  readonly name: string;

  constructor(name: string) {
    this.name = name;
  }

  /** Finds one. */
  find(query: string): string | undefined {
    if (query) {
      return undefined;
    }
  }

  #secret() {}
}
"""


class Signatures(unittest.TestCase):
    def shown(self, path, text, include_private=False):
        return [(depth, signature) for _, depth, signature, _ in docs_sig.signatures(path, text, include_private)]

    def test_java(self):
        found = docs_sig.signatures("SearchIndex.java", JAVA)
        self.assertEqual(["public class SearchIndex", "public static final int LIMIT", "public SearchIndex(int count)",
                          "public void rebuild(boolean all)", "public enum Kind", "ONE, TWO"],
                         [signature for _, _, signature, _ in found])
        self.assertEqual("A search index.", found[0][3])
        self.assertEqual("Rebuilds it.", found[3][3])
        self.assertIn("private void hidden()", [s for _, s in self.shown("SearchIndex.java", JAVA, True)])

    def test_java_member(self):
        self.assertEqual([(13, 21)], docs_sig.member_ranges("SearchIndex.java", JAVA, "rebuild"))

    def test_python(self):
        self.assertEqual([(1, "LIMIT = 10"), (1, "class Index(Base)"), (2, "size: int"),
                          (2, "def __init__(self, size)"), (2, "@staticmethod def build(items, *, fast=False) -> 'Index'")],
                         self.shown("index.py", PYTHON))
        self.assertIn((1, "def _helper()"), self.shown("index.py", PYTHON, True))
        self.assertEqual("An index.", docs_sig.signatures("index.py", PYTHON)[1][3])

    def test_python_member(self):
        self.assertEqual([(16, 19)], docs_sig.member_ranges("index.py", PYTHON, "build"))

    def test_typescript(self):
        shown = self.shown("search.ts", TYPESCRIPT)
        self.assertEqual([
            (1, "export interface SearchOptions"), (2, "query: string"), (2, "limit?: number"),
            (1, 'export type Mode = "" | ""'),
            (1, "export async function search(options: SearchOptions): Promise<string[]>"),
            (1, "export const rank = (items: string[]): number =>"),
            (1, "export class Searcher"), (2, "readonly name: string"), (2, "constructor(name: string)"),
            (2, "find(query: string): string | undefined"),
        ], shown)
        everything = [s for _, s in self.shown("search.ts", TYPESCRIPT, True)]
        self.assertIn("function internal()", everything)
        self.assertIn("private cache", everything)
        self.assertIn("#secret()", everything)
        self.assertEqual("Runs a search.", docs_sig.signatures("search.ts", TYPESCRIPT)[4][3])

    def test_typescript_member(self):
        self.assertEqual([(31, 36)], docs_sig.member_ranges("search.ts", TYPESCRIPT, "find"))
        self.assertEqual([(11, 15)], docs_sig.member_ranges("search.ts", TYPESCRIPT, "search"))

    def test_find_sources(self):
        sources = ["src/a/SearchIndex.java", "src/b/SearchIndex.java", "src/b/Other.ts"]
        self.assertEqual(["src/b/SearchIndex.java"], docs_sig.find_sources(sources, "b/SearchIndex"))
        self.assertEqual(["src/b/Other.ts"], docs_sig.find_sources(sources, "Other.ts"))

    def test_tests_by_path_and_by_diff(self):
        for path in ("tests/x.py", "src/x.test.ts", "src/test_x.py", "src/XTest.java", "a/__tests__/b.js"):
            self.assertTrue(docs_sig.is_test(path), path)
        self.assertFalse(docs_sig.is_test("src/latest.py"))
        self.assertEqual(["a block never splits"],
                         docs_sig.added_tests("XTest.java", "+    @Test\n+    void aBlockNeverSplits() {"))
        self.assertEqual(["counts facets"], docs_sig.added_tests("test_x.py", "+def test_counts_facets():"))
        self.assertEqual(["finds one"], docs_sig.added_tests("x.test.ts", "+  it('finds one', () => {"))


class Sig(Repo):
    files = {"src/search/index.py": PYTHON}

    def test_sig_and_member_through_main(self):
        _, out = self.main("sig", "index")
        self.assertIn(":8    class Index(Base)  — An index.", out)
        _, out = self.main("sig", "index:build")
        self.assertIn("== index.build  src/search/index.py:16-19", out)
        self.assertEqual(1, self.main("sig", "Missing")[0])

    def test_sig_reads_the_tools_too(self):
        self.put("tools/helper.py", "def assist(x):\n    return x\n")
        self.assertIn("def assist(x)", self.main("sig", "helper")[1])


if __name__ == "__main__":
    unittest.main()
