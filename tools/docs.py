"""Prints one block of the project's documents, so an agent reads what its task needs and no more.

Standard library only; read-only except `status`, `close`, `close-initiative`, `drop`, `record`, `raise`,
`round add`, `history add` and `ledger insert` / `ledger replace`. Settings (the package ID prefix, the
owner, budgets, source roots) come from tools/leanground.json. XX below stands for the project's prefix.
Run from the repository root:

    python tools/docs.py XX-nnn                        a Work Package: its ledger line, its block inside its
                                                       Initiative's, the open questions it names, and a menu
                                                       of the design sections and packages it cites
    python tools/docs.py help close where              only those commands' usage lines (a word no command
                                                       starts with: the lines mentioning it); help alone, all
    python tools/docs.py "Search Filters"              an Initiative: its ledger lines and its block
    python tools/docs.py 4.2.1                         a DESIGN.md section, its subsections included
    python tools/docs.py 4.2.1 --grep "cache|retry"    only its lines matching a pattern, any case, each cut to 80
                                                       characters either side of its matches; --full anywhere
                                                       in a call prints the matching lines whole
    python tools/docs.py 4.3 --own 4.3.2 7             several sections in one call, each with its own options
    python tools/docs.py --grep "cache" 4.2 4.5        a leading --grep filters every section of the call; after
                                                       a number, only that section
    python tools/docs.py q12                           open design question 12, in DESIGN.md 6.2 or a working document
    python tools/docs.py ledger                        the ledger lines alone, without the Initiatives' blocks
    python tools/docs.py working-agreements.md "Build and verify"
                                                       one heading of a document
    python tools/docs.py where-things-live.md --grep "router"
                                                       a document's lines matching a pattern; after a
                                                       heading, only that heading's lines
    python tools/docs.py where Search                  a system's paragraph in where-things-live.md: its
                                                       code, API, tests and data; a name no system has finds
                                                       the paragraphs whose text mentions it; several quoted
                                                       names at once ("recipe: route" "recipe: config") print each
    python tools/docs.py sig SearchIndex api/routes    a source file's signatures for a caller: its types,
                                                       functions, methods, fields and constants not private,
                                                       each with its line and doc comment's first sentence
                                                       (Java, Python, TypeScript and JavaScript)
    python tools/docs.py sig --all SearchIndex         private members too, for a file you will edit
    python tools/docs.py sig SearchIndex:rebuild Router
                                                       Name:member prints that member whole, its doc comment and
                                                       body with line numbers, for an edit beside it, private
                                                       or not; mix freely
    python tools/docs.py DESIGN.md                     a document's outline, with tokens per section (any
                                                       tracked document, a working document by path or name;
                                                       "outline <document>" says the same;
                                                       "outline tools/x.py" lists a script's defs and constants)
    python tools/docs.py toc DESIGN.md                 the linked list of headings its '## Contents' should hold
    python tools/docs.py tail design-history.md [N]    a document's last N non-blank lines (3 by default), whole:
                                                       the anchor for adding a row to a table's end
    python tools/docs.py check                         every cited section, question and document resolves,
                                                       the ledger agrees with its blocks, a package being built
                                                       or built has its history row, each Contents section
                                                       matches its document's headings, no open question's
                                                       number is asked twice, no tracked document outside the
                                                       archive uses a gendered pronoun, no placeholder is left
                                                       once bootstrapped, and each file an agent loads unasked
                                                       is within its budget
    python tools/docs.py budget                        those files (CLAUDE.md, AGENTS.md, skills and their stage
                                                       files, agents, skill descriptions) with tokens against
                                                       budget, their package-id anecdotes, and sentences two
                                                       of them repeat
    python tools/docs.py context                       this session's context at its last request and its peak,
                                                       from the newest transcript of this checkout, against the
                                                       size past which the package skill hands a build to a subagent
    python tools/docs.py status XX-nnn being built     writes a package's status on its ledger line, then checks
    python tools/docs.py close XX-nnn [--steps 14] [--date 2026-10-23]
                       [--delivered "the delivered search index (4.2.1)"]
                                                       closes an approved package: removes its line and block,
                                                       drops other lines' waits on it (with --delivered,
                                                       rewrites other blocks' bare mentions of it to that text,
                                                       leaving possessives to reword), adds the history row,
                                                       appends its section to its record (created if new) with
                                                       the block quoted unedited, the manual check's passing
                                                       steps and (from git) the files it changed and each test
                                                       file with its new tests as words, and TODOs for the rest
                                                       of the prose; adds it to the archive index, then checks
    python tools/docs.py close-initiative "Search Filters" [--date 2026-10-23]
                                                       closes an approved Initiative whose packages have all
                                                       closed: removes its line, Contents entry and block, drops
                                                       other lines' waits on it, writes its record's closing
                                                       (the closing line, its block quoted, a Left open TODO),
                                                       marks the index, adds a 6.4 Delivered paragraph with
                                                       TODOs for the prose and the history row, lists every
                                                       remaining mention of it or its packages, then checks
    python tools/docs.py drop q14 q9                   removes open questions, with their decisions, from
                                                       DESIGN.md 6.2 or the working document asking them,
                                                       then checks: consolidation's removal, without copying
                                                       the text into an edit; first lists each ##### note under
                                                       Open questions now left with no question, and the drop
                                                       line that would remove it (never removed unasked)
    python tools/docs.py drop DESIGN.md "D. Offline mode"
                                                       removes one heading and its block (a backlog pitch, a
                                                       finished section), then checks
    python tools/docs.py round [3]                     the earliest round in design-questions.md still asking a
                                                       question (or round 3), cut down for asking in chat
    python tools/docs.py raise draft.md                questions drafted with placeholder ids (G1, G2 ...) under
                                                       `## Questions: DESIGN.md <topic>` (a ##### topic of 6.2's
                                                       Open questions, made if new, with the draft's note) or
                                                       `## Questions: docs/initiatives/x.md`: numbers them from
                                                       6.2's next free number, rewrites G1 / QG1 / Q-G1 to
                                                       question 24 / Q24, adds them, bumps the number, checks
    python tools/docs.py round add draft.md            the same, and the draft's `## Round N (...)` part (its
                                                       `#### QG1.` headings numbered in that order) appended after
                                                       the last round, and its `## Glossary` terms the glossary
                                                       lacks added to it; writes nothing unless every part fits
    python tools/docs.py record [--by NAME] 14=rec "15=(b), because ..." "16=not yet: ..." [--date 2026-10-25]
                                                       writes each answer given into its round's Response (none
                                                       given: the Responses filled in the file), then for each
                                                       answered question writes the response under its open
                                                       question as a decision by --by (the owner by default):
                                                       complete for a plain "rec", else with a TODO for the
                                                       rule; removes it (and any topic left empty) from the
                                                       round, prints each response, then checks; "not yet" and
                                                       "discuss" stay in the round. check reports a TODO left
                                                       in a decision
    python tools/docs.py decisions q14 q15             each question's number, first sentence (up to its first
    python tools/docs.py decisions --all               "?", else 200 characters), where it is asked and its
                                                       "> **Decision ...:**" lines whole, from DESIGN.md 6.2 or
                                                       the working document: a compact brief for consolidation;
                                                       --all takes every question that has a decision
    python tools/docs.py history add rows.md           appends the markdown table rows in rows.md (one a line)
                                                       to design-history.md's table, in file order, then checks;
                                                       every row is validated first and any failure, printed with
                                                       its row number, writes nothing: a real date, three cells,
                                                       a section cited in parentheses, no gendered pronoun
    python tools/docs.py ledger insert pkg.md --after XX-12
                                                       pkg.md holds a package block (one line) and optionally its
                                                       ledger line; inserts the block after XX-12's block and the
                                                       line after XX-12's line, raising the next package ID past
                                                       the new one if needed; refuses an id already used; checks
    python tools/docs.py ledger replace XX-12 pkg.md   swaps XX-12's block (and its line, if pkg.md has one) for
                                                       pkg.md's, which must carry the same id; then checks
    python tools/docs.py orphans                       a first pass at the sweep for design no package builds:
                                                       DESIGN.md lines (sections 1 to 5, 6.7, 7 to 10, never a
                                                       Built rules subsection) saying "not built", "no package",
                                                       "post-v1" and the like, by section; then each section 4
                                                       subsection (not Built rules) no ledger block cites

A project adds commands of its own in tools/project_docs.py (see project_commands below); they are
listed after these by help.

Where a block stops. A heading's block runs to the next heading at its level or above, except
that a numbered heading nested under it (4.6.1 under 4.6) never stops it. Section numbers are
compared number by number, so 4.6 contains 4.6.1 but not 4.60, and 1 contains 1.1 but not 11.
Tokens are estimated as characters / 4.
"""

import datetime
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import docs_sig  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CONFIG = "tools/leanground.json"
DESIGN = "DESIGN.md"
LEDGER = "LEDGER.md"
WHERE = "docs/agent-notes/where-things-live.md"
HISTORY = "design-history.md"
ROUNDS = "design-questions.md"
ARCHIVE = "docs/archive/"
ARCHIVE_INDEX = "docs/archive/README.md"
RECORDS_DIR = "docs/archive/initiatives"
WORKING = "docs/initiatives/"
PLUGIN = "tools/project_docs.py"

# Read as records, not routes: their citations are of their own day, so check never follows them.
RECORDS = (HISTORY,)
# Describes the kit's placeholders, so it may name them once bootstrapped, as may every core file.
KIT_DOCS = ("LEANGROUND.md",)

LEDGER_GROUPS = ("Work-Ready", "Designed", "Undesigned")
INITIATIVES_HEADING = "Initiatives"
# Packages the owner placed outside any Initiative: an unindented line in a group, a block under this heading.
STANDALONE_HEADING = "Standalone Work Packages"
CONTENTS_HEADING = "Contents"
CONTENTS_DEPTH = 4  # a table of contents lists headings from ## down to ####
TODO = "TODO"

DEFAULTS = {
    "prefix": "XX",
    "owner": "the owner",
    "bootstrapped": False,
    "budgets": {},
    "source_roots": [],
    "subagent_build_past": 200_000,
}


def tokens(text):
    return round(len(text) / 4)


def write(path, text):
    """Writes text as UTF-8 with LF line ends, whatever the platform."""
    Path(path).write_text(text, encoding="utf-8", newline="\n")


# --- settings ----------------------------------------------------------------------------------

_configs = {}


def config(repo=REPO):
    """tools/leanground.json over DEFAULTS, read once per repository."""
    key = Path(repo).resolve()
    if key not in _configs:
        path = key / CONFIG
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        _configs[key] = {**DEFAULTS, **data}
    return _configs[key]


class Ids:
    """The patterns that depend on the project's package ID prefix."""

    def __init__(self, prefix):
        p = re.escape(prefix)
        self.prefix = prefix
        self.any = re.compile(rf"(?<![\w-]){p}-(\d+)\b")
        self.package_line = re.compile(rf"  - ({p}-(\d+)) (.+?)(?: \(([^()]+)\))?(?: — (.+))?$")
        self.standalone_line = re.compile(rf"- ({p}-(\d+)) (.+?)(?: \(([^()]+)\))?(?: — (.+))?$")
        self.package_block = re.compile(rf"- \*\*({p}-(\d+)) (.+?)\.\*\*")
        self.next_id = re.compile(rf"The next package ID is {p}-(\d+)\.")
        self.example = re.compile(rf"docs\.py (?:status |close )?({p}-\d+)\b")
        self.argument = re.compile(rf"(?i){p}-?(\d+)")
        self.record_heading = re.compile(rf"^## ({p}-\d+) ", re.MULTILINE)

    def make(self, number):
        return f"{self.prefix}-{number}"

    def parse(self, arg):
        """'XX-12', 'xx12' -> 'XX-12'; None for anything else."""
        match = self.argument.fullmatch(arg)
        return self.make(int(match.group(1))) if match else None


def ids_for(repo=REPO):
    return Ids(config(repo)["prefix"])


# --- documents ---------------------------------------------------------------------------------


class Doc:
    """One Markdown file: its lines and its headings, with fenced code skipped."""

    def __init__(self, name, text):
        self.name = name
        self.lines = text.split("\n")
        self.headings = []  # (1-based line, level, text)
        fenced = False
        for n, line in enumerate(self.lines, 1):
            if re.match(r"\s*(```|~~~)", line):
                fenced = not fenced
                continue
            match = None if fenced else re.match(r"(#{1,6})\s+(.*?)\s*$", line)
            if match:
                self.headings.append((n, len(match.group(1)), match.group(2)))

    def text(self, start, end):
        """Lines start to end, 1-based and inclusive."""
        return "\n".join(self.lines[start - 1:end])


def tracked(repo=REPO, *patterns):
    """The repository's files as git sees them: committed or staged, and new files not gitignored, so a file is
    read before its first commit. Exits with a reason outside a git repository."""
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "--deduplicate", *patterns],
                         cwd=repo, capture_output=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise SystemExit(f"{Path(repo)} is not a git repository: run git init first. ({out.stderr.strip()})")
    return [line for line in out.stdout.splitlines() if line and (Path(repo) / line).is_file()]


def tracked_markdown(repo=REPO):
    return tracked(repo, "*.md")


def load(name, repo=REPO):
    return Doc(name, (Path(repo) / name).read_text(encoding="utf-8"))


def section_number(heading):
    """'4.6.1 Built rules: Search' -> '4.6.1'; '1. Vision' -> '1'; 'Open questions' -> None."""
    match = re.match(r"(\d+(?:\.\d+)*)\.?(?:\s|$)", heading)
    return match.group(1) if match else None


def is_nested(outer, inner):
    """True when section inner sits under section outer: 4.6 holds 4.6.1, never 4.60."""
    a, b = outer.split("."), inner.split(".")
    return len(a) < len(b) and b[:len(a)] == a


def trim_end(doc, start, end):
    while end > start and not doc.lines[end - 1].strip():
        end -= 1
    return end


def heading_block(doc, heading):
    """(start, end) of a heading's block; see the module docstring for where it stops."""
    line, level, text = heading
    number = section_number(text)
    end = len(doc.lines)
    for other_line, other_level, other_text in doc.headings:
        if other_line <= line or other_level > level:
            continue
        other_number = section_number(other_text)
        if number and other_number and is_nested(number, other_number):
            continue
        end = other_line - 1
        break
    return line, trim_end(doc, line, end)


def own_block(doc, heading):
    """(start, end) of a heading's own text, up to its first subheading."""
    start, end = heading_block(doc, heading)
    first_sub = next((h[0] for h in doc.headings if start < h[0] <= end), end + 1)
    return start, trim_end(doc, start, first_sub - 1)


def subsections(doc, heading):
    """The numbered headings directly under a numbered heading: 4.9.1 and 4.9.2 under 4.9."""
    number = section_number(heading[2])
    start, end = heading_block(doc, heading)
    found = []
    for other in doc.headings:
        other_number = section_number(other[2])
        if start < other[0] <= end and other_number and is_nested(number, other_number) \
                and len(other_number.split(".")) == len(number.split(".")) + 1:
            found.append(other)
    return found


def find_section(design, number):
    for heading in design.headings:
        if section_number(heading[2]) == number:
            return heading
    return None


def section_numbers(design):
    return {section_number(h[2]) for h in design.headings if section_number(h[2])}


# --- tables of contents ------------------------------------------------------------------------


def slug(text):
    """GitHub's heading anchor: '4.7 Storage & Sync' -> '47-storage--sync'."""
    text = re.sub(r"[`*~]", "", text).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def contents_section(doc):
    """(start, end) of the lines under a document's '## Contents' heading, or None."""
    heading = next((h for h in doc.headings if h[1] == 2 and h[2] == CONTENTS_HEADING), None)
    if heading is None:
        return None
    start, end = heading_block(doc, heading)
    return start + 1, end


def expected_contents(doc):
    """The table of contents a document's headings call for: every heading after Contents, ## to ####."""
    contents = next((h for h in doc.headings if h[1] == 2 and h[2] == CONTENTS_HEADING), None)
    after = contents[0] if contents else 0
    lines = []
    seen = {}
    for line, level, text in doc.headings:
        # A repeated heading's anchor gains -1, -2 and so on, counted over the whole page.
        base = slug(text)
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchor = base if count == 0 else f"{base}-{count}"
        if line > after and 2 <= level <= CONTENTS_DEPTH and text != CONTENTS_HEADING:
            lines.append(f"{'  ' * (level - 2)}- [{text}](#{anchor})")
    return lines


def check_contents(doc):
    """A problem if the document has a Contents section that its headings no longer match."""
    section = contents_section(doc)
    if section is None:
        return []
    actual = [line for line in doc.lines[section[0] - 1:section[1]] if line.strip()]
    expected = expected_contents(doc)
    if actual == expected:
        return []
    differs = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), min(len(actual), len(expected)))
    want = expected[differs] if differs < len(expected) else "(nothing more)"
    return [(doc.name, section[0] - 1, f"Contents does not match the headings; at entry {differs + 1} it should read"
             f" {want.strip()}. Print the right one with python tools/docs.py toc {doc.name}")]


# --- open questions ----------------------------------------------------------------------------

QUESTION_LINE = re.compile(r"- \*\*(\d+)\.\*\*")


def question_items(doc, start, end):
    """Question number -> (start, end) for each `- **N.**` item between lines start and end."""
    found = {}
    n = start
    while n <= end:
        match = QUESTION_LINE.match(doc.lines[n - 1])
        if not match:
            n += 1
            continue
        # A question runs on through its indented sub-items and the owner's decisions.
        last = n
        m = n + 1
        while m <= end and (not doc.lines[m - 1].strip() or doc.lines[m - 1].startswith(" ")):
            last = m
            m += 1
        found[int(match.group(1))] = (n, trim_end(doc, n, last))
        n = m
    return found


def open_questions(design):
    """Question number -> (start, end) for each open question in DESIGN.md 6.2."""
    heading = find_section(design, "6.2")
    if heading is None:
        return {}
    return question_items(design, *heading_block(design, heading))


def working_questions(repo, files):
    """Question number -> (document, start, end) for each question asked in an Initiative's working document."""
    found = {}
    for name in files:
        if name.startswith(WORKING) and (Path(repo) / name).is_file():
            doc = load(name, repo)
            for number, span in question_items(doc, 1, len(doc.lines)).items():
                found[number] = (name, *span)
    return found


def reused_numbers(repo, files):
    """(file, line, detail) for each open question whose number an earlier one in 6.2 or a working document has."""
    design = load(DESIGN, repo)
    heading = find_section(design, "6.2")
    places = [(design, *heading_block(design, heading))] if heading else []
    places += [(doc, 1, len(doc.lines)) for doc in (load(name, repo) for name in files
                                                    if name.startswith(WORKING) and (Path(repo) / name).is_file())]
    first, problems = {}, []
    for doc, start, end in places:
        for n in range(start, end + 1):
            match = QUESTION_LINE.match(doc.lines[n - 1])
            if not match:
                continue
            number = int(match.group(1))
            if number in first:
                problems.append((doc.name, n, f"asks question {number}, which {first[number]} already asks; "
                                              "give it the next free number"))
            else:
                first[number] = f"{doc.name}:{n}"
    return problems


def question_home(repo, files, number):
    """(document, start, end) of an open question, in DESIGN.md 6.2 or a working document; None if neither."""
    found = open_questions(load(DESIGN, repo)).get(number)
    if found is not None:
        return (DESIGN, *found)
    return working_questions(repo, files).get(number)


QUESTION_CITE = re.compile(r"[Qq]uestions? (\d+(?:(?:,? and |, )\d+)*)")


def cited_questions(text):
    return sorted({int(q) for match in QUESTION_CITE.finditer(text) for q in re.findall(r"\d+", match.group(1))})


DECISION_LINE = re.compile(r"\s*>\s*\*\*[^*]*decision[^*]*:\*\*", re.IGNORECASE)
QUESTION_SHOWN = 200  # characters of a question kept when it asks nothing with a "?"


def question_asked(line):
    """A question item's first sentence: its text after the number, up to its first '?', else QUESTION_SHOWN characters."""
    text = QUESTION_LINE.sub("", line, count=1).strip()
    if "?" in text:
        return text[:text.index("?") + 1]
    return text if len(text) <= QUESTION_SHOWN else text[:QUESTION_SHOWN] + "…"


def question_decision_lines(doc, start, end):
    """The lines of a question that record a decision: each '> **...Decision...:**' line and the '>' lines continuing it."""
    found = []
    inside = False
    for n in range(start, end + 1):
        line = doc.lines[n - 1]
        if DECISION_LINE.match(line):
            inside = True
        elif not re.match(r"\s*>\s*(?!\*\*)\S", line):
            inside = False
        if inside:
            found.append(line)
    return found


# --- the ledger --------------------------------------------------------------------------------

ITEM_LINE = re.compile(r"- \*\*([^*]+)\*\*(?: — (.+))?$")
PATH_LINE = re.compile(r"  - \S+\.md$")
STATUS_WORD = re.compile(
    r"(?:[—–-]\s+|\()(work-ready|designed|undesigned|cut|built|delivered|done|in progress|next|ready|blocked)\b",
    re.IGNORECASE,
)


class Ledger:
    """LEDGER.md read as its rules state: grouped item lines, then one block per Initiative."""

    def __init__(self, doc, ids):
        self.doc = doc
        self.ids = ids
        self.items = []  # dict(line, group, name, stands)
        self.packages = []  # dict(line, id, number, name, builder, stands, owner)
        self.malformed = []  # (line, text)
        self.next_id = None
        self.next_id_line = None
        self.initiatives = {}  # name -> (start, end)
        self.blocks = {}  # package id -> dict(line, number, name, initiative)
        self.ledger_end = len(doc.lines)

        top = next((h for h in doc.headings if h[1] == 2 and h[2] == INITIATIVES_HEADING), None)
        if top is not None:
            self.ledger_end = trim_end(doc, 1, top[0] - 1)
            for heading in doc.headings:
                if heading[0] > top[0] and heading[1] == 3:
                    self.initiatives[heading[2]] = heading_block(doc, heading)

        self.contents = set()  # lines of the table of contents, which check compares with the headings instead
        group = None
        current = None
        in_contents = False
        for n in range(1, self.ledger_end + 1):
            text = doc.lines[n - 1]
            next_id = ids.next_id.search(text)
            if next_id:
                self.next_id, self.next_id_line = int(next_id.group(1)), n
            heading = re.match(r"#{1,6}\s+(.*?)\s*$", text)
            if heading:
                group = heading.group(1) if heading.group(1) in LEDGER_GROUPS else None
                in_contents = heading.group(1) == CONTENTS_HEADING
                current = None
                continue
            if in_contents:
                self.contents.add(n)
                continue
            item = ITEM_LINE.match(text)
            package = ids.package_line.match(text)
            standalone = ids.standalone_line.match(text)
            if standalone and group:
                current = None
                self.packages.append({
                    "line": n, "id": standalone.group(1), "number": int(standalone.group(2)),
                    "name": standalone.group(3).strip(), "builder": standalone.group(4),
                    "stands": standalone.group(5), "owner": STANDALONE_HEADING,
                })
            elif item and group:
                current = {"line": n, "group": group, "name": item.group(1).strip(), "stands": item.group(2)}
                self.items.append(current)
            elif package and current:
                self.packages.append({
                    "line": n, "id": package.group(1), "number": int(package.group(2)),
                    "name": package.group(3).strip(), "builder": package.group(4),
                    "stands": package.group(5), "owner": current["name"],
                })
            elif PATH_LINE.match(text) and current:
                continue
            elif re.match(r"\s*- ", text):
                self.malformed.append((n, text.strip()))

        for name, (start, end) in self.initiatives.items():
            for n in range(start, end + 1):
                match = ids.package_block.match(doc.lines[n - 1])
                if match:
                    self.blocks[match.group(1)] = {
                        "line": n, "number": int(match.group(2)), "name": match.group(3), "initiative": name,
                    }

    def item(self, name):
        return next((i for i in self.items if i["name"] == name), None)

    def package(self, package_id):
        return next((p for p in self.packages if p["id"] == package_id), None)

    def item_lines(self, name):
        """An item's ledger line with its package and path lines under it."""
        item = self.item(name)
        if item is None:
            return []
        lines = [item["line"]]
        n = item["line"] + 1
        while n <= self.ledger_end and self.doc.lines[n - 1].startswith("  - "):
            lines.append(n)
            n += 1
        return lines

    def initiative_name(self, query):
        wanted = query.strip().lower()
        return next((name for name in self.initiatives if name.lower() == wanted), None)


def load_ledger(repo=REPO, text=None):
    doc = Doc(LEDGER, text) if text is not None else load(LEDGER, repo)
    return Ledger(doc, ids_for(repo))


# --- citations ---------------------------------------------------------------------------------

DOTTED = re.compile(r"(?<![\w.])(\d+\.\d+(?:\.\d+)*)(?![\w.]*\d)")
SECTION_CITE = re.compile(r"[Ss]ections? (\d+(?:\.\d+)*)")
DESIGN_CITE = re.compile(r"DESIGN(?:\.md)?`? (?:section )?(\d+(?:\.\d+)*)")
TOUCHES = re.compile(r"\*Touches:\*([^;]*)")
MODEL_NAME = re.compile(r"Claude [A-Z]\w+ \d+(?:\.\d+)*")  # a builder's or reviewer's name, never a section
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
VERSION = re.compile(r"\bv\d+(?:\.\d+)*")


def cited_sections(text):
    """Design sections a ledger block cites: its dotted numbers, 'section N' and its Touches list."""
    text = MODEL_NAME.sub("", text)
    text = VERSION.sub("", DATE.sub("", text))
    found = set(DOTTED.findall(text))
    found.update(SECTION_CITE.findall(text))
    found.update(DESIGN_CITE.findall(text))
    for match in TOUCHES.finditer(text):
        found.update(re.findall(r"(?<![\w.])\d+(?:\.\d+)*", match.group(1)))
    return sorted(found, key=lambda s: [int(p) for p in s.split(".")])


def prose_sections(text):
    """Design sections cited in prose anywhere: 'DESIGN.md 4.6.1' and 'section 11'."""
    found = set(DESIGN_CITE.findall(text))
    found.update(SECTION_CITE.findall(text))
    return found


# --- output ------------------------------------------------------------------------------------


def header(doc, start, end, label):
    text = doc.text(start, end)
    print(f"== {label}  {doc.name}:{start}-{end}  ~{tokens(text):,} tokens")


def print_block(doc, start, end, label):
    header(doc, start, end, label)
    print()
    print(doc.text(start, end))
    print()


def section_menu_line(design, number):
    heading = find_section(design, number)
    if heading is None:
        return f"  {number:<8} not a DESIGN.md section"
    start, end = heading_block(design, heading)
    title = heading[2][len(number):].lstrip(". ")
    line = f"  {number:<8} {title}  {DESIGN}:{start}  ~{tokens(design.text(start, end)):,} tokens"
    subs = subsections(design, heading)
    if subs:
        parts = [f"own text (--own) ~{tokens(design.text(*own_block(design, heading))):,}"]
        parts += [f"{section_number(s[2])} ~{tokens(design.text(*heading_block(design, s))):,}" for s in subs]
        line += f"\n  {'':<8} of which " + "; ".join(parts)
    return line


def show_package(ledger, design, package_id):
    ids = ledger.ids
    block = ledger.blocks.get(package_id)
    line = ledger.package(package_id)
    if block is None and line is None:
        print(f"{package_id} has no ledger line and no block in {LEDGER}: it is delivered (see {HISTORY} and"
              f" {RECORDS_DIR}/) or was never claimed.")
        return 1
    doc = ledger.doc
    if line is not None:
        print(f"== Ledger line  {LEDGER}:{line['line']}")
        print()
        if line["owner"] == STANDALONE_HEADING:
            print(doc.lines[line["line"] - 1])
        else:
            for n in ledger.item_lines(line["owner"]):
                print(doc.lines[n - 1])
        print()
    if block is None:
        print(f"{package_id} has a ledger line and no block; run python tools/docs.py check.")
        return 1

    start, end = ledger.initiatives[block["initiative"]]
    siblings = [b for b in ledger.blocks.values() if b["initiative"] == block["initiative"] and b is not block]
    sibling_lines = set()
    for sibling in siblings:
        sibling_lines.update(range(sibling["line"], block_lines(doc, sibling["line"])[1] + 1))
    keep = [n for n in range(start, end + 1) if n not in sibling_lines]
    text = "\n".join(doc.lines[n - 1] for n in keep)
    print(f"== {package_id} {block['name']}, in {block['initiative']}  {LEDGER}:{start}-{end}  ~{tokens(text):,} tokens")
    if siblings:
        print("   Left out, the Initiative's other packages: "
              + "; ".join(f"{s['name']} ({ids.make(s['number'])})" for s in siblings))
    print()
    print(text)
    print()

    package_text = doc.text(*block_lines(doc, block["line"]))
    questions = open_questions(design)
    named = cited_questions(package_text + ("\n" + doc.lines[line["line"] - 1] if line else ""))
    if named:
        print("== Questions it names")
        print()
        for q in named:
            if q in questions:
                print(design.text(*questions[q]))
            else:
                print(f"- **{q}.** not open in {DESIGN} 6.2: in a working document (python tools/docs.py q{q}),"
                      f" or answered and consolidated, its reason in {HISTORY}.")
        print()

    sections = cited_sections(package_text)
    if sections:
        print("== Design sections it cites. A menu, not a reading list: open one with"
              " python tools/docs.py <number> only when the work needs it.")
        print()
        for number in sections:
            print(section_menu_line(design, number))
        print()

    others = sorted({int(n) for n in ids.any.findall(package_text)} - {block["number"]})
    if others:
        print("== Packages it names")
        print()
        for number in others:
            other = ledger.package(ids.make(number))
            name = ids.make(number)
            if other:
                print(f"  {name:<8} {other['name']}: on the ledger, {other['stands'] or 'no standing written'}")
            else:
                print(f"  {name:<8} delivered (no ledger line)")
        print()
    return 0


def show_initiative(ledger, name):
    doc = ledger.doc
    lines = ledger.item_lines(name)
    if lines:
        print(f"== Ledger lines  {LEDGER}:{lines[0]}")
        print()
        for n in lines:
            print(doc.lines[n - 1])
        print()
    print_block(doc, *ledger.initiatives[name], name)
    return 0


def outline(doc):
    whole = "\n".join(doc.lines)
    print(f"== {doc.name}  {len(doc.lines)} lines  ~{tokens(whole):,} tokens")
    print()
    for heading in doc.headings:
        start, end = heading_block(doc, heading)
        indent = "  " * (heading[1] - 1)
        print(f"  {heading[0]:>5}  {indent}{heading[2]}  (~{tokens(doc.text(start, end)):,})")
    print()
    return 0


PY_TOP = re.compile(r"(?:def (\w+)|class (\w+)|([A-Z][A-Z0-9_]*) = )")


def python_outline(path, repo=REPO):
    """A Python script's top-level functions, classes and constants with their line numbers."""
    lines = path.read_text(encoding="utf-8").split("\n")
    print(f"== {path.relative_to(repo).as_posix()}  {len(lines)} lines  ~{tokens(chr(10).join(lines)):,} tokens")
    for n, line in enumerate(lines, 1):
        top = PY_TOP.match(line)
        if top:
            shown = ("def " + top.group(1)) if top.group(1) else ("class " + top.group(2)) if top.group(2) else top.group(3)
            print(f"  {n:>5}  {shown}")
    return 0


def show_heading(doc, query):
    wanted = query.strip().lower()
    matches = [h for h in doc.headings if h[2].lower() == wanted]
    if not matches:
        matches = [h for h in doc.headings if wanted in h[2].lower()]
    if not matches:
        print(f'{doc.name} has no heading matching "{query}". Its outline:')
        print()
        outline(doc)
        return 1
    if len(matches) > 1:
        print(f'"{query}" matches {len(matches)} headings in {doc.name}; name one:')
        for heading in matches:
            print(f"  {doc.name}:{heading[0]}  {heading[2]}")
        return 1
    print_block(doc, *heading_block(doc, matches[0]), matches[0][2])
    return 0


def resolve_file(name, files):
    wanted = name.replace("\\", "/")
    if wanted in files:
        return wanted
    matches = [f for f in files if f.rsplit("/", 1)[-1] == wanted]
    return matches[0] if len(matches) == 1 else None


def show_tail(doc, count):
    """A document's last count non-blank lines with their numbers: the anchor for adding a row to a table's end."""
    lines = [(n, line) for n, line in enumerate(doc.lines, 1) if line.strip()][-count:]
    print(f"== {doc.name}: its last {len(lines)} lines")
    print()
    for n, line in lines:
        print(f"{doc.name}:{n}  {line}")
    return 0


GREP_WINDOW = 80  # characters kept either side of a match, since a paragraph is one long line
grep_window = GREP_WINDOW  # None after --full: whole lines


def grep_block(doc, start, end, pattern, window=GREP_WINDOW):
    """A block's lines matching pattern (a regular expression, any case), with their numbers, each cut to
    the text around its matches, joined by '…' where text was left out; whole lines when window is None."""
    found = re.compile(pattern, re.IGNORECASE)
    result = []
    for n in range(start, end + 1):
        line = doc.lines[n - 1]
        if window is None:
            if found.search(line):
                result.append((n, line))
            continue
        spans = []
        for match in found.finditer(line):
            low, high = max(0, match.start() - window), min(len(line), match.end() + window)
            if spans and low <= spans[-1][1]:
                spans[-1] = (spans[-1][0], high)
            else:
                spans.append((low, high))
        if spans:
            parts = [("…" if low > 0 else "") + line[low:high] + ("…" if high < len(line) else "") for low, high in spans]
            result.append((n, " ".join(parts)))
    return result


def print_grep(doc, start, end, pattern, label):
    found = grep_block(doc, start, end, pattern, grep_window)
    print(f"== {label}: lines matching {pattern}, {len(found)} of {end - start + 1}")
    print()
    for n, line in found:
        print(f"{doc.name}:{n}  {line}")


def grep_option(args):
    """Splits '--grep PATTERN' out of a document request's arguments: (the rest, the pattern or None)."""
    if "--grep" in args:
        n = args.index("--grep")
        if n + 1 < len(args):
            return args[:n] + args[n + 2:], args[n + 1].strip("\"'")
    return args, None


def section_specs(args):
    """Section requests, each a number with its own --own and --grep PATTERN: '4.3 --own 4.3.2 4.11 --grep x'
    is three, only 4.11 filtered. A '--grep PATTERN' before the first number filters every section without
    a pattern of its own: '--grep x 4.6.1 4.7.1'. A leading 'section' is allowed. None unless every argument
    fits."""
    if len(args) == 1 and " " in args[0]:
        args = args[0].split()
    if args and args[0].lower() == "section":
        args = args[1:]
    shared = None
    if len(args) >= 2 and args[0] == "--grep":
        shared, args = args[1].strip("\"'"), args[2:]
    specs, n = [], 0
    while n < len(args):
        arg = args[n]
        if re.fullmatch(r"\d+(?:\.\d+)*\.?", arg):
            specs.append([arg.rstrip("."), False, None])
        elif arg == "--own" and specs:
            specs[-1][1] = True
        elif arg == "--grep" and specs and n + 1 < len(args):
            n += 1
            specs[-1][2] = args[n].strip("\"'")
        else:
            return None
        n += 1
    return [(number, own, pattern or shared) for number, own, pattern in specs] or None


def unfiltered_note(specs):
    """When some sections of a call have a pattern and others don't, the ones printed whole, said once, since
    '4.6.1 4.7.1 --grep x' reads as filtering both but filters only 4.7.1."""
    whole = [number for number, _, pattern in specs if pattern is None]
    if whole and len(whole) < len(specs):
        return (f"Note: --grep filters only the section before it, so {', '.join(whole)} printed whole."
                " Put --grep first to filter every section: --grep PATTERN 4.6.1 4.7.1")
    return None


def show_section(design, heading, own, pattern):
    if pattern:
        start, end = (own_block if own else heading_block)(design, heading)
        print_grep(design, start, end, pattern, heading[2])
        return
    if not own:
        print_block(design, *heading_block(design, heading), heading[2])
        return
    print_block(design, *own_block(design, heading), heading[2] + ", without its subsections")
    subs = subsections(design, heading)
    if subs:
        print("== Its subsections")
        print()
        for sub in subs:
            print(section_menu_line(design, section_number(sub[2])))
        print()


# --- where things live -------------------------------------------------------------------------

LEAD = re.compile(r"\*\*(.+?)\*\*")


def where_paragraphs(doc, name):
    """Lines of where-things-live.md whose bold lead names the system: '**Search** (4.2…' for 'search'.
    Each system is one paragraph on one line."""
    wanted = name.strip().lower()
    return [n for n, line in enumerate(doc.lines, 1)
            if LEAD.match(line) and wanted in LEAD.match(line).group(1).lower()]


def where_mentions(doc, name):
    """System paragraphs whose text mentions the name, for one no system is named."""
    wanted = name.strip().lower()
    return [n for n, line in enumerate(doc.lines, 1) if LEAD.match(line) and wanted in line.lower()]


def show_where(doc, name):
    found = where_paragraphs(doc, name)
    if not found:
        found = where_mentions(doc, name)
        if found:
            print(f'No system in {doc.name} is named "{name}"; these paragraphs mention it.')
            print()
    if not found:
        leads = [LEAD.match(line).group(1) for line in doc.lines if LEAD.match(line)]
        print(f'No system in {doc.name} is named or mentions "{name}".'
              + (f" Systems: {', '.join(leads)}." if leads else " It lists no systems yet."))
        return 1
    for n in found:
        print(f"{doc.name}:{n}  {doc.lines[n - 1]}")
        print()
    return 0


def where_names(doc, args):
    """The names a where request asks for: its words as one name when a system is named so (unquoted), else
    each argument on its own ("recipe: route" "recipe: config")."""
    joined_name = " ".join(args)
    return [joined_name] if len(args) == 1 or where_paragraphs(doc, joined_name) else list(args)


def show_where_all(doc, args):
    return max([show_where(doc, name) for name in where_names(doc, args)])


# --- check -------------------------------------------------------------------------------------


def check_ledger(ledger, design, all_ids, asked_elsewhere=()):
    """The ledger's own rules (working-agreements.md, "Initiatives and Work Packages"), as problems.

    asked_elsewhere holds the questions open in working documents, which a ledger line may name as well.
    """
    problems = []
    ids = ledger.ids

    def report(line, detail):
        problems.append((LEDGER, line, detail))

    for line, text in ledger.malformed:
        report(line, f'"{text}" is not a ledger line the format allows')
    for n in range(1, ledger.ledger_end + 1):
        text = ledger.doc.lines[n - 1]
        if n in ledger.contents:
            continue
        if re.match(r"\s*\|.*\|\s*$", text):
            report(n, "the ledger holds a table row; it is written as plain lines")
        elif re.search(r"\]\([^)]*\)", text):
            report(n, "the ledger holds a link; names are searched for, not linked")

    seen = {}
    for item in ledger.items:
        if item["name"] in seen:
            report(item["line"], f"{item['name']} is listed twice, first at line {seen[item['name']]}")
        seen.setdefault(item["name"], item["line"])
        if item["name"] not in ledger.initiatives:
            report(item["line"], f'"{item["name"]}" has no block under {INITIATIVES_HEADING}')
        if item["group"] != "Undesigned" and not item["stands"]:
            report(item["line"], f"{item['name']} is {item['group']} and does not say where it stands")
    for name, (start, _) in ledger.initiatives.items():
        if name not in seen and name != STANDALONE_HEADING:
            report(start, f'"{name}" has a block and no ledger line')
        word = STATUS_WORD.search(name)
        if word:
            report(start, f'heading "{name}" carries the status word "{word.group(1)}"; standing is on the ledger line only')

    found_ids = {}
    for package in ledger.packages:
        if package["id"] in found_ids:
            report(package["line"], f"{package['id']} is repeated, first at line {found_ids[package['id']]}")
        found_ids.setdefault(package["id"], package["line"])
        block = ledger.blocks.get(package["id"])
        if block is None:
            report(package["line"], f"{package['id']} has a ledger line and no block")
            continue
        if block["name"] != package["name"]:
            report(package["line"], f"{package['id']} is named \"{package['name']}\", but its block says \"{block['name']}\"")
        if block["initiative"] != package["owner"]:
            report(block["line"], f"{package['id']} is under {package['owner']} on the ledger, but its block is in {block['initiative']}")
    for package_id, block in ledger.blocks.items():
        if package_id not in found_ids:
            report(block["line"], f"{package_id} has a block and no ledger line")

    if ledger.next_id is None:
        report(1, f'the ledger does not state "The next package ID is {ids.prefix}-n."')
    elif all_ids and ledger.next_id <= max(all_ids):
        report(ledger.next_id_line, f"the next ID {ids.make(ledger.next_id)} is not above {ids.make(max(all_ids))},"
                                    " already used")

    questions = open_questions(design)
    for n in range(1, ledger.ledger_end + 1):
        for q in cited_questions(ledger.doc.lines[n - 1]):
            if q not in questions and q not in asked_elsewhere:
                report(n, f"question {q} is named on a ledger line but is not open in {DESIGN} 6.2"
                          " or a working document")
    for start, end in ledger.initiatives.values():
        for n in range(start, end + 1):
            for q in cited_questions(ledger.doc.lines[n - 1]):
                if q not in questions and q not in asked_elsewhere:
                    report(n, f"a block names question {q}, which is not open; once it is consolidated, cite the"
                              " section that holds its rule")

    # A wait on something closed is stale: close drops it, and this catches what close missed. Waits on
    # package ids and on names (capitalised, as Initiatives are) are checked; a wait on prose is not.
    names = {item["name"] for item in ledger.items}
    for entry in ledger.items + ledger.packages:
        for target in wait_targets(entry["stands"]):
            named = ids.any.fullmatch(target) or target[:1].isupper()
            if named and target not in found_ids and target not in names:
                report(entry["line"], f'waits on "{target}", which is not on the ledger')
    return problems


PRONOUN = re.compile(r"\b(he|him|his|himself|she|her|hers|herself)\b", re.IGNORECASE)
PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}|<!-- bootstrap:")


def unfenced_matches(doc, pattern):
    """(line, match text) for the first match of pattern on each line of a document, fenced code skipped."""
    found = []
    fenced = False
    for n, line in enumerate(doc.lines, 1):
        if re.match(r"\s*(```|~~~)", line):
            fenced = not fenced
        elif not fenced:
            match = pattern.search(line)
            if match:
                found.append((n, match.group(0)))
    return found


def source_files(repo, sources=None):
    """Tracked source files under the configured source roots, in a language sig reads."""
    roots = config(repo)["source_roots"]
    names = tracked(repo) if sources is None else sources
    return [name for name in names if Path(name).suffix in docs_sig.ADAPTERS
            and (not roots or any(name.startswith(root.rstrip("/") + "/") for root in roots))]


def find_problems(repo, files, sources=()):
    """Everything check reports, as (file, line, detail), and a one-line summary.

    files are the tracked Markdown and sources the tracked source files, both relative to repo.
    """
    repo = Path(repo)
    settings = config(repo)
    ids = Ids(settings["prefix"])
    problems = []
    design = load(DESIGN, repo)
    ledger = Ledger(load(LEDGER, repo), ids)
    numbers = section_numbers(design)
    basenames = {f.rsplit("/", 1)[-1] for f in files}

    all_ids = set()
    for name in files:
        text = ids.next_id.sub("", (repo / name).read_text(encoding="utf-8"))
        all_ids.update(int(n) for n in ids.any.findall(text))
    problems += check_ledger(ledger, design, all_ids, working_questions(repo, files))
    problems += check_budgets(repo, files)
    problems += reused_numbers(repo, files)

    live = [f for f in files if not f.startswith(ARCHIVE) and f not in RECORDS]
    cited = 0
    for name in live:
        doc = load(name, repo)
        problems += check_contents(doc)
        for n, text in enumerate(doc.lines, 1):
            if STUB in text:
                problems.append((name, n, "an owner decision still holds record's TODO; write the rule as decided"))
            sections = cited_sections(text) if name == LEDGER and n > ledger.ledger_end else prose_sections(text)
            for number in sections:
                cited += 1
                if number not in numbers:
                    problems.append((name, n, f"cites section {number}, which {DESIGN} does not have"))
            for match in re.finditer(r"`([\w./-]+\.md)`", text):
                target = match.group(1)
                exists = (repo / target).exists() if "/" in target else target in basenames
                if not exists:
                    problems.append((name, n, f"names {target}, which is not a tracked document"))

    # The records are checked too: their rows are written by history add, which refuses a pronoun.
    for name in files:
        if not name.startswith(ARCHIVE):
            for n, pronoun in unfenced_matches(load(name, repo), PRONOUN):
                problems.append((name, n, f'uses the gendered pronoun "{pronoun}"; write they, them or the name'))

    # Once bootstrapped, every placeholder and bootstrap comment has been filled in.
    left = 0
    for name in live:
        if name in KIT_DOCS or is_core(repo, name):
            continue
        for n, found in unfenced_matches(load(name, repo), PLACEHOLDER):
            left += 1
            if settings["bootstrapped"]:
                problems.append((name, n, f"still holds {found}; fill it in (the bootstrap skill says how)"))
    if settings["bootstrapped"] and "{{" in json.dumps({k: v for k, v in settings.items() if k != "core"}):
        problems.append((CONFIG, 1, "still holds a {{placeholder}}; set the project's values"))

    # A package under way has its rules' history row, written in the same turn as its status.
    history = (repo / HISTORY).read_text(encoding="utf-8") if (repo / HISTORY).exists() else ""
    for package in ledger.packages:
        if (package["stands"] or "").startswith(("being built", "built")) and not re.search(
                rf"^\| \d{{4}}-\d{{2}}-\d{{2}} \| {re.escape(package['id'])}\b", history, re.MULTILINE):
            problems.append((LEDGER, package["line"], f"{package['id']} is {package['stands']} but {HISTORY} has no"
                             f" row for it; add its rules' row with history add"))

    # Examples must stay runnable: a closed package's id in one goes stale at its close.
    on_ledger = {package["id"] for package in ledger.packages}
    for name in live:
        for n, text in enumerate((repo / name).read_text(encoding="utf-8").split("\n"), 1):
            for package_id in ids.example.findall(text):
                if package_id not in on_ledger:
                    problems.append((name, n, f"gives {package_id} as an example, which is not on the ledger;"
                                              f" write {ids.prefix}-nnn"))

    for name in sources:
        path = repo / name
        if not path.is_file():
            continue
        for n, text in enumerate(path.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            for number in DESIGN_CITE.findall(text):
                cited += 1
                if number not in numbers:
                    problems.append((name, n, f"cites DESIGN {number}, which {DESIGN} does not have"))

    extra = plugin(repo)
    if extra is not None and hasattr(extra, "problems"):
        problems += extra.problems(repo, files)

    summary = (f"Checked {len(ledger.items)} ledger items, {len(ledger.packages)} packages and {cited} section"
               f" citations across {len(live)} documents and {len(sources)} source files.")
    if left and not settings["bootstrapped"]:
        summary += f" Not bootstrapped yet: {left} placeholders wait for the bootstrap skill."
    return problems, summary


# --- token budgets -----------------------------------------------------------------------------

# Files an agent loads without asking: CLAUDE.md, AGENTS.md and every skill's description in each session,
# a SKILL.md when its skill is invoked, a stage file beside it when its stage starts, an agent definition
# when its subagent starts. Every later turn resends them, so check fails on one over its budget. Budgets
# live in tools/leanground.json; trim before raising one, and raising one is the owner's call.
SKILLS = ".claude/skills/"
AGENTS = ".claude/agents/"
UNLOADED = ("why.md",)  # read only to challenge a rule, never to follow one
DESCRIPTION_BUDGET = 120  # a skill's description is in every session's skill listing
NEAR_BUDGET = 0.9
REPEAT_WORDS = 10  # a sentence this long, found in two loaded files, is paid for twice
# Not budgeted, but read beside the skills, so a sentence a skill shares with them is reported too.
REPEAT_SOURCES = ("docs/agent-notes/working-agreements.md",)


def budgeted(repo, files):
    listed = config(repo)["budgets"]
    return [f for f in files if f in ("CLAUDE.md", "AGENTS.md") or f in listed
            or (f.startswith((SKILLS, AGENTS)) and f.endswith(".md") and f.rsplit("/", 1)[-1] not in UNLOADED)]


def skill_description(text):
    match = re.match(r"---\r?\n(?:.*\n)*?description:\s*(.*)\r?\n(?:.*\n)*?---\r?\n", text)
    return match.group(1) if match else None


def repeated_sentences(texts):
    """Sentences of REPEAT_WORDS or more found in two or more of texts ({name: text}), as {sentence: [names]}."""
    seen = {}
    for name, text in texts.items():
        for sentence in re.split(r"(?<=[.!?:])\s+|\n", text):
            words = [w for w in re.sub(r"[`*_]", "", sentence).lower().split() if re.search(r"\w", w)]
            if len(words) >= REPEAT_WORDS:
                seen.setdefault(" ".join(words), [])
                if name not in seen[" ".join(words)]:
                    seen[" ".join(words)].append(name)
    return {sentence: names for sentence, names in seen.items() if len(names) > 1}


def loaded_together(names):
    """Whether two of these files share a context: the session holds CLAUDE.md, AGENTS.md, the skills and
    REPEAT_SOURCES; a subagent holds its own definition and CLAUDE.md, never another agent's or a skill."""
    session = [name for name in names if not name.startswith(AGENTS)]
    agents = [name for name in names if name.startswith(AGENTS)]
    return len(session) >= 2 or bool(agents and {"CLAUDE.md", "AGENTS.md"} & set(session))


def budget_repeats(repo, files, texts):
    """repeated_sentences across the budgeted texts and REPEAT_SOURCES that a budgeted file holds, where two of
    the files holding it are loaded together."""
    also = {name: (Path(repo) / name).read_text(encoding="utf-8") for name in REPEAT_SOURCES if name in files}
    return {sentence: where for sentence, where in repeated_sentences({**texts, **also}).items()
            if any(name in texts for name in where) and loaded_together(where)}


def check_budgets(repo, files):
    problems = []
    budgets = config(repo)["budgets"]
    texts = {name: (Path(repo) / name).read_text(encoding="utf-8") for name in budgeted(repo, files)}
    for name, text in texts.items():
        if name not in budgets:
            problems.append((name, 1, f"has no token budget; add one under budgets in {CONFIG}"))
        elif tokens(text) > budgets[name]:
            problems.append((name, 1, f"is ~{tokens(text):,} tokens, over its budget of {budgets[name]:,};"
                                      " trim it (the rule, not the story) before raising the budget"))
        description = skill_description(text) if name.endswith("/SKILL.md") else None
        if description is not None and tokens(description) > DESCRIPTION_BUDGET:
            problems.append((name, 3, f"its description is ~{tokens(description)} tokens, over {DESCRIPTION_BUDGET}"))
    for sentence, where in budget_repeats(repo, files, texts).items():
        problems.append((where[1], 1, f'repeats a sentence of {where[0]}: "{sentence[:70]}…"; keep it in one'))
    return problems


def show_budgets(repo, files):
    budgets = config(repo)["budgets"]
    anecdote = ids_for(repo).any
    names = budgeted(repo, files)
    texts = {name: (Path(repo) / name).read_text(encoding="utf-8") for name in names}
    width = max([len(name) for name in names] + [4])
    print(f"  {'file':{width}}  tokens  budget  used  anecdotes")
    for name, text in texts.items():
        budget = budgets.get(name)
        used = tokens(text) / budget if budget else None
        mark = "" if used is None or used < NEAR_BUDGET else ("  OVER" if used > 1 else "  near")
        shown = f"{budget:6,}  {used:4.0%}" if budget else "  none     -"
        print(f"  {name:{width}}  {tokens(text):6,}  {shown}  {len(anecdote.findall(text)):9}{mark}")
    for name, text in texts.items():
        description = skill_description(text) if name.endswith("/SKILL.md") else None
        if description is not None:
            print(f"  description of {name}: ~{tokens(description)} of {DESCRIPTION_BUDGET} tokens, every session")
    for sentence, where in budget_repeats(repo, files, texts).items():
        print(f'  repeated in {", ".join(where)}: "{sentence[:80]}…"')
    return 0


# --- context: how much each later request resends ----------------------------------------------


def transcript_dir(repo):
    """Claude Code's transcript folder for a checkout: its path with every other character a dash."""
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(Path(repo).resolve()))


def context_use(lines):
    """(requests, prompt tokens of the last request, peak) from a transcript's lines, one per API response."""
    seen, last, peak = set(), 0, 0
    for line in lines:
        if '"usage"' not in line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get("message") or {}
        usage = message.get("usage")
        if entry.get("type") != "assistant" or not usage or message.get("id") in seen:
            continue
        seen.add(message.get("id"))
        last = (usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0))
        peak = max(peak, last)
    return len(seen), last, peak


def show_context(repo):
    folder = transcript_dir(repo)
    transcripts = sorted(folder.glob("*.jsonl"), key=lambda path: path.stat().st_mtime) if folder.is_dir() else []
    if not transcripts:
        print(f"No transcripts in {folder} (a session started in another folder keeps them there). Judge by the"
              " plan instead: past about 20 files, the build goes to subagents.")
        return 1
    newest = transcripts[-1]
    requests, last, peak = context_use(newest.read_text(encoding="utf-8", errors="replace").splitlines())
    past = config(repo)["subagent_build_past"]
    print(f"session {newest.stem[:8]}: {last // 1000}k of context at the last request, peak {peak // 1000}k,"
          f" {requests} requests")
    print(f"at the rules commit, past {past // 1000}k a subagent builds (the package skill)")
    return 0


def is_core(repo, name):
    """A file the kit owns (tools/leanground.json's core list): its examples cite no project's design."""
    return any(name == entry or (entry.endswith("/") and name.startswith(entry)) for entry in config(repo).get("core", []))


def check(files, repo=REPO):
    sources = [name for name in source_files(repo) if not is_core(repo, name)]
    problems, summary = find_problems(repo, files, sources)
    print(summary)
    if not problems:
        print("Everything resolves.")
        return 0
    print()
    for name, line, detail in problems:
        print(f"  {name}:{line}  {detail}")
    print()
    print(f"{len(problems)} problems.")
    return 1


# --- writing: a package's status ---------------------------------------------------------------


def set_status(text, package_id, status, ids):
    """The ledger text with the package line's words after its dash replaced by status."""
    led = Ledger(Doc(LEDGER, text), ids)
    package = led.package(package_id)
    if package is None:
        raise ValueError(f"{package_id} has no ledger line.")
    lines = text.split("\n")
    line = lines[package["line"] - 1]
    head = line.split(" — ", 1)[0]
    lines[package["line"] - 1] = f"{head} — {status}"
    return "\n".join(lines)


# --- writing: dropping questions and headings, recording a round's answers ---------------------

RESPONSE = "> **Response:**"
DEFERRED = re.compile(r"(?i)\W*(not yet|discuss)\b")
STUB = "TODO: the rule as decided, whether it overrules the recommendation and why, what is unverified."


def remove_lines(lines, start, end):
    """lines without start to end (1-based, inclusive), and without the blank line that would then be doubled."""
    before, after = lines[:start - 1], lines[end:]
    if after and not after[0].strip() and (not before or not before[-1].strip()):
        after = after[1:]
    return before + after


def drop_questions(text, name, numbers):
    """text without the question items numbered numbers; in DESIGN.md only 6.2's count."""
    doc = Doc(name, text)
    spans = open_questions(doc) if name == DESIGN else question_items(doc, 1, len(doc.lines))
    missing = [str(n) for n in numbers if n not in spans]
    if missing:
        raise ValueError(f"{name} has no open question {', '.join(missing)}.")
    lines = doc.lines
    for number in sorted(numbers, key=lambda q: spans[q][0], reverse=True):
        lines = remove_lines(lines, *spans[number])
    return "\n".join(lines)


def drop_heading(text, name, query):
    """(text without the one heading query names and its block, that heading's text)."""
    doc = Doc(name, text)
    matches = [h for h in doc.headings if query.lower() in h[2].lower()]
    exact = [h for h in matches if h[2].lower() == query.lower()]
    matches = exact if len(exact) == 1 else matches
    if len(matches) != 1:
        named = "; ".join(h[2] for h in matches[:8])
        raise ValueError(f'"{query}" names {len(matches)} headings in {name}; name one{": " + named if named else ""}.')
    return "\n".join(remove_lines(doc.lines, *heading_block(doc, matches[0]))), matches[0][2]


def round_answers(doc):
    """(number, response, start, end) for each #### Q question in the rounds file, its Response as one line."""
    found = []
    for heading in doc.headings:
        match = re.match(r"Q(\d+)\.", heading[2])
        if heading[1] != 4 or not match:
            continue
        start, end = heading_block(doc, heading)
        response = []
        for n in range(start, end + 1):
            line = doc.lines[n - 1]
            if line.startswith(RESPONSE):
                response.append(line[len(RESPONSE):].strip())
            elif response and line.startswith(">"):
                response.append(line[1:].strip())
            elif response:
                break
        found.append((int(match.group(1)), " ".join(part for part in response if part), start, end))
    return found


def empty_topics(doc):
    """(start, end) of each ### topic inside a ## Round that no longer holds a question."""
    spans = []
    for heading in doc.headings:
        parent = next((h for h in reversed(doc.headings) if h[0] < heading[0] and h[1] == 2), None)
        if heading[1] != 3 or parent is None or not parent[2].startswith("Round"):
            continue
        start, end = heading_block(doc, heading)
        if not any(h[1] == 4 and start < h[0] <= end for h in doc.headings):
            spans.append((start, end))
    return spans


ACCEPTED = re.compile(r"(?i)\W*rec(ommendation)?\W*$")


def decision_stub(date, response, by):
    """The decision written under a question: complete for a plain "rec", else a TODO for the rule as decided."""
    if ACCEPTED.match(response):
        return f"  > **Decision ({date}, {by}):** Accepts the recommendation. Not yet consolidated."
    return f'  > **Decision ({date}, {by}):** {STUB} The response: "{response}". Not yet consolidated.'


def write_responses(text, answers):
    """The rounds file with each answered question's Response set to its answer (a bare "rec" written as
    "Recommendation."); answers maps question number to answer. Raises ValueError for a number not asked there."""
    doc = Doc(ROUNDS, text)
    asked = {number: (start, end) for number, _, start, end in round_answers(doc)}
    missing = sorted(set(answers) - set(asked))
    if missing:
        raise ValueError(f"{ROUNDS} asks no question {', '.join(map(str, missing))}.")
    lines = list(doc.lines)
    for number in sorted(answers, key=lambda q: asked[q][0], reverse=True):
        start, end = asked[number]
        at = next((n for n in range(start, end + 1) if lines[n - 1].startswith(RESPONSE)), None)
        if at is None:
            raise ValueError(f"Q{number} in {ROUNDS} has no Response line.")
        last = at
        while last < end and lines[last].startswith(">"):
            last += 1
        answer = "Recommendation." if ACCEPTED.match(answers[number]) else answers[number]
        lines[at - 1:last] = [f"{RESPONSE} {answer}"]
    return "\n".join(lines)


def record_answers(repo, files, date, by, answers=None):
    """Writes answers (question number -> answer) into the rounds file's Responses, then writes each answered
    round question's response under its open question as a decision by by, and removes the question, and any
    topic left empty, from the rounds file. Returns what was done."""
    repo = Path(repo)
    if answers:
        path = repo / ROUNDS
        write(path, write_responses(path.read_text(encoding="utf-8"), answers))
    rounds = load(ROUNDS, repo)
    done, recorded, by_home = [], [], {}
    for number, response, start, end in round_answers(rounds):
        if not response:
            continue
        if DEFERRED.match(response):
            done.append(f"Q{number} stays in {ROUNDS} for the next round: {response}")
            continue
        home = question_home(repo, files, number)
        if home is None:
            done.append(f"Q{number} is open neither in {DESIGN} 6.2 nor a working document; left in {ROUNDS}")
            continue
        by_home.setdefault(home[0], {})[number] = response
        recorded.append((start, end))
    for name, by_number in by_home.items():
        doc = load(name, repo)
        spans = open_questions(doc) if name == DESIGN else question_items(doc, 1, len(doc.lines))
        lines = doc.lines
        for number in sorted(by_number, key=lambda q: spans[q][1], reverse=True):
            at = spans[number][1]
            lines = lines[:at] + [decision_stub(date, by_number[number], by)] + lines[at:]
        write(repo / name, "\n".join(lines))
        done += [f"Q{number} recorded under its question in {name}: {by_number[number]}"
                 for number in sorted(by_number)]
    lines = rounds.lines
    for start, end in sorted(recorded, reverse=True):
        lines = remove_lines(lines, start, end)
    for start, end in sorted(empty_topics(Doc(ROUNDS, "\n".join(lines))), reverse=True):
        lines = remove_lines(lines, start, end)
    lines, finished = remove_answered_rounds(lines)
    done += [f"{name} asks nothing more: removed, and listed as answered" for name in finished]
    write(repo / ROUNDS, "\n".join(lines))
    return done


ANSWERED = "Answered rounds:"


def remove_answered_rounds(lines):
    """(lines without each ## Round left asking no question, the rounds' names), each named on the
    'Answered rounds:' line, whose 'none yet.' the first replaces."""
    doc = Doc(ROUNDS, "\n".join(lines))
    finished = []
    for heading in reversed([h for h in doc.headings if h[1] == 2 and re.match(r"Round \d+", h[2])]):
        start, end = heading_block(doc, heading)
        if not any(h[1] == 4 and start < h[0] <= end for h in doc.headings):
            lines = remove_lines(lines, start, end)
            finished.insert(0, re.match(r"Round \d+(?: \([\d-]+\))?", heading[2]).group(0))
    if finished:
        at = next((n for n, line in enumerate(lines) if line.startswith(ANSWERED)), None)
        if at is None:
            lines += ["", f"{ANSWERED} {', '.join(finished)}."]
        else:
            listed = lines[at][len(ANSWERED):].strip().rstrip(".")
            names = ([] if listed in ("", "none yet") else [listed]) + finished
            lines[at] = f"{ANSWERED} {', '.join(names)}."
    return lines, finished


def chat_round(doc, number=None):
    """Round number's block, or the earliest round still asking a question, cut down for asking in chat: no blank
    lines, Options labels, empty Responses or "Cost of being wrong" tails. None if there is no such round."""
    rounds = [h for h in doc.headings if h[1] == 2 and h[2].startswith("Round")]
    for heading in rounds:
        start, end = heading_block(doc, heading)
        named = re.match(r"Round (\d+)\b", heading[2])
        asks = any(h[1] == 4 and start < h[0] <= end and h[2].startswith("Q") for h in doc.headings)
        if (number is None and asks) or (number is not None and named and int(named.group(1)) == number):
            kept = []
            for line in doc.lines[start - 1:end]:
                if not line.strip() or line.strip() in ("**Options:**", RESPONSE):
                    continue
                kept.append(line.split(" Cost of being wrong:")[0] if line.startswith("**Recommendation:**") else line)
            return "\n".join(kept)
    return None


# --- writing: waits ----------------------------------------------------------------------------


def wait_items(body):
    """The things a 'waits on' list names: 'questions 1 and 2, XX-1 and XX-3' is
    ['questions 1 and 2', 'XX-1', 'XX-3']; a list without commas splits at its last 'and'."""
    parts = body.split(", ")
    return [item.strip() for item in parts[:-1] + parts[-1].rsplit(" and ", 1)]


def wait_targets(stands):
    """Every package id and ledger item a line's standing waits on; questions are left out."""
    targets = []
    for segment in (stands or "").split("; "):
        match = re.match(r"waits on (.+)$", segment.strip())
        if match:
            targets += [item for item in wait_items(match.group(1))
                        if not re.match(r"(questions? |\d)", item)]
    return targets


def drop_wait(stands, package_id):
    """A status without its wait on package_id: 'waits on XX-1 and XX-2' less XX-1 is 'waits on XX-2', and
    'waits on questions 1 and 2, XX-1, XX-3 and XX-4' less XX-1 is 'waits on questions 1 and 2, XX-3 and XX-4'."""
    match = re.match(r"waits on (.+)$", stands or "")
    if not match:
        return stands
    items = wait_items(match.group(1))
    if package_id not in items:
        items = match.group(1).split(" and ")
    rest = [item for item in items if item.strip() != package_id]
    if not rest:
        return "can be built"
    return "waits on " + (rest[0] if len(rest) == 1 else ", ".join(rest[:-1]) + " and " + rest[-1])


def drop_waits(stands, target, empty="can be built"):
    """A standing without its wait on target, in any of its '; ' parts: 'no open questions; waits on X' less X
    is 'no open questions'. With nothing left, empty."""
    kept = []
    for segment in (stands or "").split("; "):
        if segment.startswith("waits on ") and target in wait_items(segment[len("waits on "):]):
            segment = drop_wait(segment, target)
            if segment == "can be built":
                continue
        kept.append(segment)
    return "; ".join(kept) if kept else empty


# --- writing: a package's close ----------------------------------------------------------------


def block_lines(doc, line):
    """A package block: its line and any indented lines continuing it."""
    end = line
    while end < len(doc.lines) and doc.lines[end].startswith("  ") and doc.lines[end].strip():
        end += 1
    return line, end


def naming_fields(line, package_id):
    """The fields of a block line ('*Touches:* …', '*Depends on:* …') that name package_id, so the closer
    sees what to rewrite without opening the ledger. The text before the first field counts as one."""
    fields = re.split(r"\s+(?=\*[A-Z][^*]*:\*)", line.strip())
    return [field for field in fields if package_id in field]


def deliver_mentions(line, package_id, delivered):
    """A block line with each bare mention of package_id replaced by delivered ('the delivered search index
    (4.2.1)'). A possessive ("XX-nnn's panel") is left for the closer, who rewords it."""
    return re.sub(rf"(?<![\w-]){re.escape(package_id)}(?!\d)(?!'s)", delivered, line)


def remove_package(text, package_id, ids, delivered=None):
    """The ledger without the package's line and block, and with other lines' waits on it dropped. With
    delivered, other blocks' bare mentions of it are rewritten to that text (deliver_mentions).
    Returns (new text, the block as it stood, the package's line fields, notes for the closer)."""
    doc = Doc(LEDGER, text)
    led = Ledger(doc, ids)
    package = led.package(package_id)
    block = led.blocks.get(package_id)
    if package is None or block is None:
        raise ValueError(f"{package_id} needs both a ledger line and a block to close.")
    start, end = block_lines(doc, block["line"])
    block_text = doc.text(start, end)
    notes = []
    lines = list(doc.lines)
    for other in led.packages:
        if other["id"] != package_id and package_id in (other["stands"] or ""):
            new = drop_waits(other["stands"], package_id)
            n = other["line"] - 1
            lines[n] = lines[n].split(" — ", 1)[0] + f" — {new}"
            notes.append(f"{other['id']} now reads: {new}")
    drop = {package["line"]} | set(range(start, end + 1))
    for other_id, other in led.blocks.items():
        line = doc.lines[other["line"] - 1]
        if other_id != package_id and package_id in line:
            # The line as it will stand once the closed package's lines are gone.
            at = other["line"] - sum(1 for n in drop if n < other["line"])
            if delivered:
                line = deliver_mentions(line, package_id, delivered)
                lines[other["line"] - 1] = line
                notes.append(f"{other_id}'s block now names {delivered} ({LEDGER}:{at}).")
            if package_id in line:
                notes.append(f"{other_id}'s block still names {package_id}; edit its text by hand ({LEDGER}:{at}):")
                notes += [f"    {field}" for field in naming_fields(line, package_id)]
    kept = [line for n, line in enumerate(lines, 1) if n not in drop]
    return "\n".join(kept), block_text, package, notes


def record_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def code_list(names):
    return ", ".join(f"`{name}`" for name in names)


def record_section(package_id, name, builder, date, block, steps=None, changes=None):
    """A package's record section. What close knows is filled in (the manual check's steps, and from git the
    files and tests the package changed); the prose is left as TODOs."""
    changes = changes or {}
    quoted = "\n".join("> " + line if line else ">" for line in block.split("\n"))
    changed = f" (these changed: {code_list(changes['files'])})" if changes.get("files") else ""
    commits = f" Its commits: {'; '.join(changes['commits'])}." if changes.get("commits") else ""
    tests = changes.get("tests", {})
    if changes.get("test_files"):
        tested = ", ".join(f"`{path}` ({'; '.join(tests[path])})" if tests.get(path) else f"`{path}` (updated)"
                           for path in changes["test_files"])
    else:
        tested = f"{TODO}: the tests that cover it, or why none were added"
    manual = (f"all {steps} steps passed: {TODO}, what was seen." if steps
              else f"none; {TODO}: why no manual check was needed.")
    return (f"## {package_id} {name}\n\n"
            f"Built and approved on {date} by {builder}. Rules in `{DESIGN}` {TODO}: the sections and what each holds.\n\n"
            "### The package as approved for building\n\n"
            f"From `{LEDGER}`, unedited:\n\n{quoted}\n\n"
            "### What was built\n\n"
            f"- {TODO}: the rules, then each code change by file{changed}, then any fixtures and debug controls.{commits}\n\n"
            "### Verification\n\n"
            f"- Tests: {tested}.\n"
            f"- Manual check: {manual}\n")


START_COMMIT = "start building"


def package_changes(repo, package_id):
    """What the package changed, from its first commit (subject led by its id) to HEAD: the source files and
    test files under the source roots (or anywhere outside docs), the tests each test file gained, and the
    subjects of its commits after the first, without the id and name. Empty without git or commits."""
    def git(*args):
        # Git writes UTF-8 whatever the console's code page; text=True alone decodes cp1252 on Windows.
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, encoding="utf-8", errors="replace",
                              check=True).stdout
    roots = config(repo)["source_roots"] or ["."]
    try:
        # --grep matches any line of a message, so a body line naming the id would match too: subjects only.
        log = [line for line in git("log", "--reverse", "--format=%H %s", "-E", "--grep", f"^{package_id} ").splitlines()
               if line.split(" ", 1)[-1].startswith(f"{package_id} ")]
        first = log[0].split()[0] if log else None
        names = git("diff", "--name-only", f"{first}^", "HEAD", "--", *roots).splitlines() if first else []
        names = [name for name in names if Path(name).suffix in docs_sig.ADAPTERS]
        diffs = {path: git("diff", "-U0", f"{first}^", "HEAD", "--", path) for path in names if docs_sig.is_test(path)}
    except (OSError, subprocess.CalledProcessError):
        return {}
    subjects = [line.split(" ", 1)[1].split(": ", 1)[-1] for line in log if " " in line]
    return {
        "files": [name for name in names if not docs_sig.is_test(name)],
        "test_files": [name for name in names if docs_sig.is_test(name)],
        "tests": {path: docs_sig.added_tests(path, diff) for path, diff in diffs.items()},
        "commits": [s for s in subjects if not s.startswith(START_COMMIT)],
    }


def record_header(owner, standalone):
    if standalone:
        return (f"# {owner} — delivery record\n\n"
                "A standalone Work Package outside any Initiative, recorded when the owner approved it. "
                f"Its rules are in `{DESIGN}` {TODO}.\n\n")
    return (f"# {owner} — delivery record\n\n"
            "The Initiative's record, opened when its first Work Package was approved. One block per package, "
            f"added as each is approved. Its rules are in `{DESIGN}` {TODO} and the Built rules each package names.\n\n")


def index_entry(text, record, owner, package_id, name, date, standalone):
    """The archive index with the package added to its record's line, or a new line for a new record."""
    lines = text.split("\n")
    entry = f"{package_id} {name} ({date})"
    for n, line in enumerate(lines):
        if f"`{record}`" in line:
            lines[n] = line.rstrip().rstrip(".") + f", {entry}."
            return "\n".join(lines)
    kind = "a standalone Work Package outside any Initiative" if standalone else "open, one block per package"
    new = f"- `{record}`: {owner}, {kind}; {entry}."
    # The first entry replaces the index's "None yet."
    empty = next((n for n, line in enumerate(lines) if line.strip() == "None yet."
                  and any(l.strip() == "## Index" for l in lines[:n])), None)
    if empty is not None:
        lines[empty] = new
        return "\n".join(lines)
    folder = record.rsplit("/", 1)[0]
    last = max((n for n, line in enumerate(lines) if line.startswith(f"- `{folder}/")), default=None)
    at = last + 1 if last is not None else len(lines)
    lines.insert(at, new)
    return "\n".join(lines)


def append_row(text, row):
    """A table document with row added after its last table row."""
    return append_history(text, [row])


def close_package(repo, package_id, date, steps=None, delivered=None):
    """Closes an approved package: the ledger, the history row, the record and the archive index.
    Returns what was done, line by line."""
    repo = Path(repo)
    ids = ids_for(repo)
    ledger_path = repo / LEDGER
    text, block, package, notes = remove_package(ledger_path.read_text(encoding="utf-8"), package_id, ids, delivered)
    owner = package["owner"]
    standalone = owner == STANDALONE_HEADING
    title = package["name"] if standalone else owner
    folder = repo / RECORDS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    existing = sorted(folder.glob(f"*-{record_slug(title)}-record.md"))
    path = existing[0] if existing else folder / f"{date}-{record_slug(title)}-record.md"
    record = path.relative_to(repo / ARCHIVE).as_posix()
    section = record_section(package_id, package["name"], package["builder"] or TODO, date, block, steps,
                             package_changes(repo, package_id))

    write(ledger_path, text)
    if existing:
        body = path.read_text(encoding="utf-8").rstrip("\n")
        write(path, body + "\n\n" + section)
    else:
        write(path, record_header(title, standalone) + section)
    checked = f"after the manual check, all {steps} steps passing" if steps else "with no manual check"
    row = (f"| {date} | {package_id} approved and leaves the ledger; its block joins the {title} record "
           f"({LEDGER}) | Owner approval {checked} |")
    history = repo / HISTORY
    write(history, append_row(history.read_text(encoding="utf-8"), row))
    index = repo / ARCHIVE_INDEX
    write(index, index_entry(index.read_text(encoding="utf-8"), record, title, package_id,
                             package["name"], date, standalone))
    return [f"Removed {package_id}'s ledger line and block.", f"Added the history row to {HISTORY}.",
            f"{'Appended to' if existing else 'Created'} {path.relative_to(repo).as_posix()}; fill its {TODO}s.",
            f"Added {package_id} to {ARCHIVE_INDEX}."] + notes


# --- writing: an Initiative's close ------------------------------------------------------------

COUNT_WORDS = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve")


def joined(items):
    """'a', 'a and b', 'a, b and c'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def id_ranges(package_ids, ids):
    """Package ids as a phrase, three or more in a row as a range: 'XX-100 to XX-105 and XX-120'."""
    numbers = sorted(int(package_id.rsplit("-", 1)[1]) for package_id in package_ids)
    runs = []
    for number in numbers:
        if runs and number == runs[-1][-1] + 1:
            runs[-1].append(number)
        else:
            runs.append([number])
    parts = []
    for run in runs:
        parts += [f"{ids.make(run[0])} to {ids.make(run[-1])}"] if len(run) >= 3 else [ids.make(n) for n in run]
    return joined(parts)


def remove_initiative(text, name, ids):
    """The ledger without the Initiative's line, its Contents entry and its block, and with other lines' waits
    on it dropped. Returns (new text, the block's text without its heading, the lines that waited on it, notes).
    Refused while any of its packages is still on the ledger."""
    doc = Doc(LEDGER, text)
    led = Ledger(doc, ids)
    if led.item(name) is None or name not in led.initiatives:
        raise ValueError(f'"{name}" needs both a ledger line and a block to close.')
    left = [package["id"] for package in led.packages if package["owner"] == name]
    if left:
        raise ValueError(f"{name} still has {joined(left)} on the ledger; close those first.")
    drop = set(led.item_lines(name))
    notes = [f"Its working document {doc.lines[n - 1].strip()[2:]}: move it unedited to {RECORDS_DIR}/ beside the "
             "record, with the same date prefix." for n in drop if PATH_LINE.match(doc.lines[n - 1])]
    drop |= {n for n in led.contents if re.match(rf"\s*- \[{re.escape(name)}\]\(#", doc.lines[n - 1])}
    start, end = led.initiatives[name]
    while end < len(doc.lines) and not doc.lines[end].strip():
        end += 1
    drop |= set(range(start, end + 1))
    body_start = start + 1
    while body_start <= end and not doc.lines[body_start - 1].strip():
        body_start += 1
    body = doc.text(body_start, trim_end(doc, body_start, end))

    lines = list(doc.lines)
    freed = []
    for entry in led.items + led.packages:
        if name in wait_targets(entry["stands"]):
            empty = "can be built" if "id" in entry else "no open questions"
            new = drop_waits(entry["stands"], name, empty)
            n = entry["line"] - 1
            lines[n] = lines[n].split(" — ", 1)[0] + f" — {new}"
            who = entry.get("id") or entry["name"]
            freed.append(who)
            notes.append(f"{who} now reads: {new}")
    kept = [line for n, line in enumerate(lines, 1) if n not in drop]
    return "\n".join(kept), body, freed, notes


def mentions(repo, files, words, skip=()):
    """Each line of files naming any of words, as 'file:line  text around it', for the hand edits a close leaves."""
    pattern = re.compile("|".join(rf"(?<![\w-]){re.escape(word)}(?![\w-])" for word in words))
    found = []
    for name in files:
        if name.startswith(ARCHIVE) or name in RECORDS or name in skip or not (Path(repo) / name).exists():
            continue
        for n, line in enumerate((Path(repo) / name).read_text(encoding="utf-8").split("\n"), 1):
            match = pattern.search(line)
            if match:
                a, b = max(0, match.start() - 80), min(len(line), match.end() + 80)
                found.append(f"  {name}:{n}  {'…' if a else ''}{line[a:b].strip()}{'…' if b < len(line) else ''}")
    return found


def close_initiative(repo, name, date, files=()):
    """Closes an approved Initiative whose packages have all closed: the ledger, its record's closing, the
    archive index, a 6.4 Delivered paragraph, the history row. Returns what was done and every remaining
    mention of it or its packages in files, for the hand edits."""
    repo = Path(repo)
    ids = ids_for(repo)
    ledger_path = repo / LEDGER
    text, body, freed, notes = remove_initiative(ledger_path.read_text(encoding="utf-8"), name, ids)
    existing = sorted((repo / RECORDS_DIR).glob(f"*-{record_slug(name)}-record.md"))
    if not existing:
        raise ValueError(f"{name} has no record in {RECORDS_DIR}; close its packages first.")
    path = existing[0]
    record = path.read_text(encoding="utf-8")
    if "\nDelivered and closed on " in record:
        raise ValueError(f"{path.name} already says it is closed.")
    package_ids = ids.record_heading.findall(record)
    if not package_ids:
        raise ValueError(f"{path.name} records no package.")
    ranges = id_ranges(package_ids, ids)
    count = COUNT_WORDS[len(package_ids)] if len(package_ids) < len(COUNT_WORDS) else str(len(package_ids))
    quoted = "\n".join("> " + line if line else ">" for line in body.split("\n"))
    closing = (f"Delivered and closed on {date} by owner approval, after {package_ids[-1]}. "
               f"{count} package{'s' if len(package_ids) != 1 else ''}: {ranges}.\n\n"
               f"## The Initiative as cut\n\nFrom `{LEDGER}`, unedited:\n\n{quoted}\n\n"
               f"### Left open at closing\n\n- {TODO}: what stays open (questions, loose ends) and what moved to which"
               " other Initiative.\n\n")
    at = record.find("\n\n## ")
    record = record[:at + 2] + closing + record[at + 2:] if at >= 0 else record.rstrip("\n") + "\n\n" + closing

    index_path = repo / ARCHIVE_INDEX
    record_name = path.relative_to(repo / ARCHIVE).as_posix()
    index_lines = index_path.read_text(encoding="utf-8").split("\n")
    start = date
    for n, line in enumerate(index_lines):
        if f"`{record_name}`" in line:
            index_lines[n] = line.replace(", open, one block per package", f", closed {date}, one block per package")
            first = re.search(r"\((\d{4}-\d{2}-\d{2})\)", line)
            start = first.group(1) if first else date

    design = load(DESIGN, repo)
    delivered = find_section(design, "6.4")
    if delivered is None:
        raise ValueError(f"{DESIGN} has no section 6.4.")
    span = date if start == date else f"{start} to {date}"
    paragraph = (f"**{name}** ({span}): {TODO}: what a user now has. Packages {ranges}. Rules in {TODO}; record "
                 f"`{path.relative_to(repo).as_posix()}`. {TODO}: what stays open, and what moved to which Initiative.")
    design_lines = list(design.lines)
    d_start, d_end = heading_block(design, delivered)
    # The first paragraph replaces the section's "None yet."
    empty = next((n for n in range(d_start, d_end + 1) if design_lines[n - 1].strip() == "None yet."), None)
    if empty is not None:
        design_lines[empty - 1] = paragraph
    else:
        design_lines[d_end:d_end] = ["", paragraph]

    waits = "".join(f"; {who} no longer waits on it" for who in freed)
    row = (f"| {date} | {name} closes: it leaves the ledger and joins 6.4 Delivered ({ranges}){waits} "
           f"| Owner approval after {package_ids[-1]} |")

    write(ledger_path, text)
    write(path, record)
    write(index_path, "\n".join(index_lines))
    write(repo / DESIGN, "\n".join(design_lines))
    history = repo / HISTORY
    write(history, append_row(history.read_text(encoding="utf-8"), row))

    found = [line for line in mentions(repo, files, [name] + package_ids) if paragraph[:60] not in line]
    done = [f"Removed {name}'s ledger line, Contents entry and block.",
            f"Closed {path.relative_to(repo).as_posix()}: the closing line, the Initiative as cut, and a {TODO} under"
            " Left open at closing.",
            f"Marked it closed in {ARCHIVE_INDEX}.",
            f"Added its paragraph to {DESIGN} 6.4 Delivered, with {TODO}s for the prose and its rule sections.",
            f"Added the history row to {HISTORY}."] + notes
    if found:
        done += ["", "Still naming it or its packages (refresh examples; a delivered dependency reads"
                 ' "the delivered <thing> (<section>)"):'] + found
    return done


# --- writing: history rows and package blocks --------------------------------------------------

HISTORY_DATE = re.compile(r"\| (\d{4}-\d{2}-\d{2}) \|")
# A decision cell cites its section as existing rows do: (4.10), (4.2, 4.2.1), (section 1), (LEDGER.md).
HISTORY_CITE = re.compile(r"\([^()]*(?:(?<![\w-])\d{1,2}(?:\.\d+)*(?![\w-])|LEDGER\.md|DESIGN\.md)[^()]*\)")


def history_problems(rows):
    """(row number, detail) for each way a design-history row fails the table's shape; rows are 1-based."""
    problems = []
    for n, row in enumerate(rows, 1):
        start = HISTORY_DATE.match(row)
        if not start:
            problems.append((n, "does not start with | YYYY-MM-DD |"))
            continue
        try:
            datetime.date.fromisoformat(start.group(1))
        except ValueError:
            problems.append((n, f"{start.group(1)} is not a real date"))
        cells = re.split(r"(?<!\\)\|", row.rstrip())
        if len(cells) != 5 or cells[0].strip() or cells[4].strip() or not all(cell.strip() for cell in cells[1:4]):
            problems.append((n, "needs exactly three filled cells between pipes: date, decision, reason"))
        elif not HISTORY_CITE.search(cells[2]):
            problems.append((n, "its decision cites no section in parentheses, such as (4.10) or (LEDGER.md)"))
        pronoun = PRONOUN.search(row)
        if pronoun:
            problems.append((n, f'uses the gendered pronoun "{pronoun.group(1)}"; write they, them or the name'))
    return problems


def append_history(text, rows):
    """The history text with rows added after its table's last row."""
    lines = text.split("\n")
    last = max((n for n, line in enumerate(lines) if line.startswith("|")), default=None)
    if last is None:
        raise ValueError(f"{HISTORY} has no table to add rows to.")
    return "\n".join(lines[:last + 1] + rows + lines[last + 1:])


def package_file(text, ids):
    """(block line, ledger line or None, package id) from a package file: the block, and optionally its ledger
    line. Raises ValueError for any other shape."""
    lines = [line.rstrip() for line in text.split("\n") if line.strip()]
    blocks = [line for line in lines if ids.package_block.match(line)]
    entries = [line for line in lines if ids.package_line.match(line) or ids.standalone_line.match(line)]
    if len(blocks) != 1 or len(entries) > 1 or len(blocks) + len(entries) != len(lines):
        raise ValueError(f"The file holds one package block (- **{ids.prefix}-m Name.** *Outcome:* ...) and optionally"
                         f" its ledger line (  - {ids.prefix}-m Name (Claude ...) — status), nothing else.")
    block = ids.package_block.match(blocks[0])
    if entries:
        entry = ids.package_line.match(entries[0]) or ids.standalone_line.match(entries[0])
        if (entry.group(1), entry.group(3).strip()) != (block.group(1), block.group(3)):
            raise ValueError(f'The ledger line says {entry.group(1)} "{entry.group(3).strip()}", the block'
                             f' {block.group(1)} "{block.group(3)}".')
    return blocks[0], entries[0] if entries else None, block.group(1)


def insert_package(text, new, after, ids):
    """The ledger with the file's package block right after after's block and its ledger line, if it has one,
    right after after's line; the next package ID is raised past it if needed."""
    block, entry, package_id = package_file(new, ids)
    doc = Doc(LEDGER, text)
    led = Ledger(doc, ids)
    if package_id in led.blocks or led.package(package_id):
        raise ValueError(f"{package_id} is already on the ledger.")
    anchor, anchor_line = led.blocks.get(after), led.package(after)
    if anchor is None or (entry and anchor_line is None):
        raise ValueError(f"{after} needs both a ledger line and a block to insert after.")
    lines = list(doc.lines)
    number = int(package_id.rsplit("-", 1)[1])
    if led.next_id is not None and led.next_id <= number:
        lines[led.next_id_line - 1] = ids.next_id.sub(f"The next package ID is {ids.make(number + 1)}.",
                                                      lines[led.next_id_line - 1])
    adds = [(block_lines(doc, anchor["line"])[1], [block])]
    if entry:
        adds.append((anchor_line["line"], [entry]))
    for at, add in sorted(adds, reverse=True):
        lines[at:at] = add
    return "\n".join(lines)


def replace_package(text, package_id, new, ids):
    """The ledger with package_id's block, and its ledger line if the file has one, replaced by the file's."""
    block, entry, new_id = package_file(new, ids)
    if new_id != package_id:
        raise ValueError(f"The file holds {new_id}, not {package_id}.")
    doc = Doc(LEDGER, text)
    led = Ledger(doc, ids)
    old, old_line = led.blocks.get(package_id), led.package(package_id)
    if old is None or (entry and old_line is None):
        raise ValueError(f"{package_id} needs both a ledger line and a block to replace.")
    lines = list(doc.lines)
    start, end = block_lines(doc, old["line"])
    lines[start - 1:end] = [block]
    if entry:
        lines[old_line["line"] - 1] = entry
    return "\n".join(lines)


# --- writing: raising drafted questions and adding a drafted round -----------------------------

DRAFT_ITEM = re.compile(r"- \*\*([A-Z]+\d+)\.\*\*")
DRAFT_ASKED = re.compile(r"#### Q-?([A-Z]+\d+)\.")
NEXT_FREE = re.compile(r"(next free number: \*\*)(\d+)(\*\*)")
GLOSSARY_INTRO = "**A short glossary**"
GLOSSARY_TERM = re.compile(r"- \*\*(.+?):?\*\*")
OPEN_QUESTIONS = "Open questions"


def draft_parts(text):
    """(where, note lines, question items, round lines or None, glossary items) from a draft: a
    `## Questions: <where>` part (an optional note paragraph, then `- **G1.**` items with placeholder ids), an
    optional `## Round N (...)` part and an optional `## Glossary` part. Raises ValueError for any other shape."""
    doc = Doc("draft", text)
    where = note = items = round_lines = None
    glossary = []
    for heading in (h for h in doc.headings if h[1] == 2):
        start, end = heading_block(doc, heading)
        body = doc.lines[start:end]
        if heading[2].startswith("Questions:"):
            if where is not None:
                raise ValueError("The draft has two `## Questions:` parts; raise each topic from a draft of its own.")
            where, note, items = heading[2].split(":", 1)[1].strip(), [], []
            for line in body:
                if line.startswith("- **"):
                    items.append([line])
                elif items and (line.startswith(" ") or not line.strip()):
                    items[-1].append(line)
                elif not items and line.strip():
                    note.append(line)
            items = [item[:trim_end(Doc("item", "\n".join(item)), 1, len(item))] for item in items]
        elif heading[2].startswith("Round "):
            round_lines = [doc.lines[start - 1]] + body
        elif heading[2].startswith("Glossary"):
            glossary = [line for line in body if line.startswith("- **")]
        else:
            raise ValueError(f'The draft\'s "## {heading[2]}" is none of Questions:, Round or Glossary.')
    if not items and round_lines is None:
        raise ValueError("The draft has no `## Questions: <where>` part with `- **G1.**` items, and no round.")
    items = items or []
    bad = [item[0][:40] for item in items if not DRAFT_ITEM.match(item[0])]
    if bad:
        raise ValueError(f"These items have no placeholder id such as **G1.**: {'; '.join(bad)}")
    return where, note, items, round_lines, glossary


def draft_numbers(items, round_lines, first):
    """Placeholder id -> permanent number from first on: in the round's order, then the items' order."""
    found = [DRAFT_ITEM.match(item[0]).group(1) for item in items]
    asked = [m.group(1) for line in round_lines or [] for m in [DRAFT_ASKED.match(line)] if m]
    unknown = [q for q in asked if q not in found]
    if unknown or len(set(found)) != len(found):
        raise ValueError(f"The round asks {', '.join(unknown)}, which no item raises." if unknown
                         else "Two items share a placeholder id.")
    order = asked + [q for q in found if q not in asked]
    return {q: first + n for n, q in enumerate(order)}


def renumber(text, numbers, cite):
    """text with each placeholder in numbers replaced: an item's **G1.** by its number, a list after "question" or
    "questions" (G1, G2 and G3) by bare numbers, Q-G1 or QG1 by Q24, any other G1 by cite(24)."""
    placeholders = "|".join(sorted(map(re.escape, numbers), key=len, reverse=True))
    one = rf"(?:Q-?)?(?:{placeholders})"
    bare = lambda m: re.sub(rf"(?:Q-?)?({placeholders})", lambda k: str(numbers[k.group(1)]), m.group(2))  # noqa: E731
    text = re.sub(rf"\*\*({placeholders})\.\*\*", lambda m: f"**{numbers[m.group(1)]}.**", text)
    text = re.sub(rf"(\b[Qq]uestions?\s+)({one}(?:(?:,\s*|,?\s+and\s+|\s+to\s+){one})*)(?!\w)",
                  lambda m: m.group(1) + bare(m), text)
    text = re.sub(rf"(?<![\w-])Q-?({placeholders})(?!\w)", lambda m: f"Q{numbers[m.group(1)]}", text)
    return re.sub(rf"(?<![\w-])({placeholders})(?!\w)", lambda m: cite(numbers[m.group(1)]), text)


def append_questions(doc, heading, note, bullets):
    """doc's lines with bullets added at the end of heading's block; a note, which goes before them, only where
    the heading asks nothing yet. A lone 'None yet.' under the heading is replaced."""
    start, end = heading_block(doc, heading)
    asks = any(QUESTION_LINE.match(doc.lines[n - 1]) for n in range(start, end + 1))
    if note and asks:
        raise ValueError(f'"{heading[2]}" already asks questions: leave the note out, or edit the heading\'s note.')
    lines = list(doc.lines)
    placeholder = next((n for n in range(start + 1, end + 1) if lines[n - 1].strip() == "None yet."), None)
    if placeholder is not None:
        lines[placeholder - 1:placeholder] = (note + [""] if note else []) + bullets
        return lines
    lines[end:end] = bullets if asks else [""] + (note + [""] if note else []) + bullets
    return lines


def raise_into(repo, where, note, bullets):
    """(document, its new text) with bullets raised where says: `DESIGN.md <topic>` under 6.2's Open questions,
    that ##### topic made if new; or a working document's ## Open questions."""
    repo = Path(repo)
    if where.startswith(DESIGN):
        topic = where[len(DESIGN):].strip()
        if not topic:
            raise ValueError("Questions: DESIGN.md names its ##### topic under 6.2's Open questions.")
        design = load(DESIGN, repo)
        section = find_section(design, "6.2")
        if section is None:
            raise ValueError(f"{DESIGN} has no section 6.2.")
        start, end = heading_block(design, section)
        opened = next((h for h in design.headings if start < h[0] <= end and h[1] == 4 and h[2] == OPEN_QUESTIONS),
                      None)
        if opened is None:
            raise ValueError(f"{DESIGN} 6.2 has no #### {OPEN_QUESTIONS}.")
        o_start, o_end = heading_block(design, opened)
        found = next((h for h in design.headings
                      if o_start < h[0] <= o_end and h[1] == 5 and h[2].lower() == topic.lower()), None)
        if found:
            return DESIGN, "\n".join(append_questions(design, found, note, bullets))
        lines = list(design.lines)
        placeholder = next((n for n in range(o_start + 1, o_end + 1) if lines[n - 1].strip() == "None yet."), None)
        if placeholder is not None:
            lines[placeholder - 1:placeholder] = [f"##### {topic}", ""] + (note + [""] if note else []) + bullets
        else:
            lines[o_end:o_end] = ["", f"##### {topic}", ""] + (note + [""] if note else []) + bullets
        return DESIGN, "\n".join(lines)
    if not where.startswith(WORKING) or not (repo / where).is_file():
        raise ValueError(f'"{where}" is neither "DESIGN.md <topic>" nor a working document under {WORKING}.')
    doc = load(where, repo)
    opened = next((h for h in doc.headings if h[1] == 2 and h[2] == OPEN_QUESTIONS), None)
    if opened is None:
        raise ValueError(f"{where} has no ## {OPEN_QUESTIONS}.")
    return where, "\n".join(append_questions(doc, opened, note, bullets))


def append_round(text, round_lines):
    """The rounds file with round_lines added after its last round, the first at the file's end; the new round's
    number must be the highest."""
    doc = Doc(ROUNDS, text)
    rounds = [h for h in doc.headings if h[1] == 2 and re.match(r"Round \d+", h[2])]
    new = int(re.match(r"## Round (\d+)", round_lines[0]).group(1))
    last = max((int(re.match(r"Round (\d+)", h[2]).group(1)) for h in rounds), default=0)
    if new <= last:
        raise ValueError(f"The draft is round {new}, but {ROUNDS} already has round {last}.")
    at = heading_block(doc, rounds[-1])[1] if rounds else trim_end(doc, 1, len(doc.lines))
    lines = list(doc.lines)
    trimmed = round_lines[:trim_end(Doc("round", "\n".join(round_lines)), 1, len(round_lines))]
    lines[at:at] = [""] + trimmed
    return "\n".join(lines)


def merge_glossary(text, items):
    """(the rounds file with each glossary item whose term it lacks added after its glossary's last term, the
    terms skipped as already there)."""
    lines = text.split("\n")
    intro = next((n for n, line in enumerate(lines) if line.startswith(GLOSSARY_INTRO)), None)
    if intro is None:
        raise ValueError(f"{ROUNDS} has no line starting {GLOSSARY_INTRO}.")
    first = next(n for n in range(intro + 1, len(lines)) if lines[n].strip())
    last = first
    while last < len(lines) and lines[last].startswith("- **"):
        last += 1
    known = {GLOSSARY_TERM.match(line).group(1).lower() for line in lines[first:last]}
    added, skipped = [], []
    for item in items:
        term = GLOSSARY_TERM.match(item).group(1)
        if term.lower() in known:
            skipped.append(term)
        else:
            added.append(item)
            known.add(term.lower())
    if first == last and added:
        lines[first:first] = added + [""]  # the glossary's first terms
    else:
        lines[last:last] = added
    return "\n".join(lines), skipped


def add_draft(repo, source, with_round):
    """Raises a draft's questions with permanent numbers, bumps 6.2's next free number and, with with_round, adds
    its round and glossary terms to the rounds file. Writes nothing unless every part fits. Returns what was done."""
    repo = Path(repo)
    where, note, items, round_lines, glossary = draft_parts(Path(source).read_text(encoding="utf-8"))
    if with_round and round_lines is None:
        raise ValueError("round add needs a `## Round N (...)` part in the draft; raise takes questions alone.")
    if not with_round and round_lines is not None:
        raise ValueError("The draft has a round: use round add, which adds the round and its glossary too.")
    design_text = (repo / DESIGN).read_text(encoding="utf-8")
    free = NEXT_FREE.search(design_text)
    if free is None:
        raise ValueError(f"{DESIGN} 6.2 states no next free number.")
    # A round may also ask questions raised earlier, by their numbers: each must be open.
    raised = [int(m.group(1)) for line in round_lines or [] for m in [re.match(r"#### Q(\d+)\.", line)] if m]
    missing = sorted(set(raised) - set(all_questions(repo, tracked_markdown(repo))))
    if missing:
        raise ValueError(f"The round asks question {', '.join(map(str, missing))}, which is not open.")
    numbers = draft_numbers(items, round_lines, int(free.group(2)))
    writes, done = {}, []
    if items:
        ordered = sorted(items, key=lambda item: numbers[DRAFT_ITEM.match(item[0]).group(1)])
        bullets = renumber("\n".join(line for item in ordered for line in item), numbers,
                           lambda n: f"question {n}").split("\n")
        name, text = raise_into(repo, where, renumber("\n".join(note), numbers, lambda n: f"question {n}").split("\n")
                                if note else [], bullets)
        last = max(numbers.values())
        writes[name] = text
        design_text = writes.get(DESIGN, design_text)
        writes[DESIGN] = NEXT_FREE.sub(lambda m: f"{m.group(1)}{last + 1}{m.group(3)}", design_text, count=1)
        done += [f"{q} is question {n}" for q, n in sorted(numbers.items(), key=lambda pair: pair[1])]
        done.append(f"Raised questions {min(numbers.values())} to {last} in {name}; the next free number is {last + 1}.")
    if with_round:
        rounds_text = append_round((repo / ROUNDS).read_text(encoding="utf-8"),
                                   renumber("\n".join(round_lines), numbers, lambda n: f"Q{n}").split("\n")
                                   if numbers else round_lines)
        rounds_text, skipped = merge_glossary(rounds_text, glossary)
        writes[ROUNDS] = rounds_text
        done.append(f"Added {round_lines[0][3:]} to {ROUNDS}"
                    + (f"; glossary terms already there, edit by hand if they need amending: {', '.join(skipped)}"
                       if skipped else "."))
    for name, text in writes.items():
        write(repo / name, text)
    return done


# --- reading: decisions and the sweep for unbuilt design ---------------------------------------


def all_questions(repo, files):
    """Question number -> (document, start, end) for every open question, in DESIGN.md 6.2 or a working document."""
    found = {number: (DESIGN, *span) for number, span in open_questions(load(DESIGN, repo)).items()}
    for number, home in working_questions(repo, files).items():
        found.setdefault(number, home)
    return found


def show_decisions(repo, files, numbers):
    """Each question's brief: number, first sentence, where it is asked and its decision lines. numbers is a list,
    or None for every question that has a decision."""
    questions = all_questions(repo, files)
    docs = {}
    shown, missing = 0, False
    for number in sorted(questions) if numbers is None else numbers:
        if number not in questions:
            print(f"q{number} is not open in {DESIGN} 6.2 or a working document.")
            missing = True
            continue
        name, start, end = questions[number]
        doc = docs.setdefault(name, load(name, repo))
        decisions = question_decision_lines(doc, start, end)
        if numbers is None and not decisions:
            continue
        shown += 1
        print(f"q{number}  {question_asked(doc.lines[start - 1])}  [{name}:{start}{' (6.2)' if name == DESIGN else ''}]")
        for line in decisions or ["no decision written"]:
            print(f"    {line.strip()}")
        print()
    if numbers is None and not shown:
        print("No open question has a decision written.")
    return 1 if missing else 0


def empty_notes(design):
    """The ##### notes under 6.2's Open questions that no question bullet is left in, as headings."""
    section = find_section(design, "6.2")
    if section is None:
        return []
    start, end = heading_block(design, section)
    found, parent = [], None
    for heading in design.headings:
        if not start < heading[0] <= end:
            continue
        if heading[1] == 4:
            parent = heading[2]
        elif heading[1] == 5 and parent == OPEN_QUESTIONS:
            first, last = heading_block(design, heading)
            if not any(QUESTION_LINE.match(design.lines[n - 1]) for n in range(first, last + 1)):
                found.append(heading)
    return found


def report_empty_notes(text):
    """Prints each note left with no question and the drop line that would remove it; never removes one."""
    design = Doc(DESIGN, text)
    for heading in empty_notes(design):
        pointer = " It points at a working document, so it may stay." \
            if WORKING in design.text(*heading_block(design, heading)) else ""
        print(f'{DESIGN}:{heading[0]}  the note "{heading[2]}" has no question left.{pointer}'
              f' To remove it: python tools/docs.py drop {DESIGN} "{heading[2]}"')


ORPHAN_WORDS = re.compile(
    r"not built|no package|later package|later initiative|post-v1|until .{0,60} is built|later convenience"
    r"|stretch|is not decided|remain open|waits for play", re.IGNORECASE)
ORPHAN_SECTIONS = ("1", "2", "3", "4", "5", "7", "8", "9", "10")
ORPHAN_WIDTH = 160
BUILT_RULES = "Built rules"


def orphan_section(trail):
    """The numbered section a line sits in, if the sweep reads it: 1 to 5, 6.7 and 7 to 10, never a Built rules one."""
    if any(BUILT_RULES in text for text in trail):
        return None
    number = next((section_number(text) for text in reversed(trail) if section_number(text)), None)
    if number and (number.split(".")[0] in ORPHAN_SECTIONS or number == "6.7" or number.startswith("6.7.")):
        return number
    return None


def around(line, match, width=ORPHAN_WIDTH):
    """A line cut to width characters around a match, with '…' where text was left out."""
    if len(line) <= width:
        return line
    low = max(0, min(match.start() - (width - len(match.group())) // 2, len(line) - width))
    return ("…" if low else "") + line[low:low + width] + ("…" if low + width < len(line) else "")


def design_trails(design):
    """For each line of the design (1-based), the texts of the headings it sits under, outermost first."""
    levels = {h[0]: h for h in design.headings}
    stack, trails = [], {}
    for n in range(1, len(design.lines) + 1):
        if n in levels:
            while stack and stack[-1][1] >= levels[n][1]:
                stack.pop()
            stack.append((levels[n][2], levels[n][1]))
        trails[n] = tuple(text for text, _ in stack)
    return trails


def unbuilt_lines(design):
    """section number -> (title, [(line, text)]) for the design lines the sweep's phrases match."""
    trails = design_trails(design)
    headings = {h[0] for h in design.headings}
    found = {}
    fenced = False
    for n, line in enumerate(design.lines, 1):
        if re.match(r"\s*(```|~~~)", line):
            fenced = not fenced
        match = ORPHAN_WORDS.search(line)
        if fenced or n in headings or not match or line.lstrip().startswith("<!--"):
            continue
        number = orphan_section(trails[n])
        if number:
            title = next(text for text in reversed(trails[n]) if section_number(text) == number)
            found.setdefault(number, (title, []))[1].append((n, around(line, match)))
    return found


def uncited_subsections(design, ledger):
    """The headings of section 4's unbuilt subsections that no ledger block, an Initiative's or a package's, cites.

    A subsection is built when its heading says so or a Built rules subsection sits under it; its
    unbuilt lines are the line sweep's to find."""
    text = ledger.doc.text(1, len(ledger.doc.lines))
    cited = set(DOTTED.findall(text)) | set(cited_sections(text))
    trails = design_trails(design)
    numbers = [(section_number(h[2]) or "", h[2]) for h in design.headings]

    def built(number, title):
        return "(built)" in title or any(n.startswith(number + ".") and BUILT_RULES in t for n, t in numbers)

    return [h for h in design.headings
            if (section_number(h[2]) or "").startswith("4.") and section_number(h[2]) not in cited
            and not any(BUILT_RULES in text for text in trails[h[0]])
            and not built(section_number(h[2]), h[2])]


def show_orphans(design, ledger):
    found = unbuilt_lines(design)
    print(f"== Lines saying design is not built, {sum(len(lines) for _, lines in found.values())} in {len(found)} sections")
    for number, (title, lines) in found.items():
        print()
        print(f"{title}  ({len(lines)})")
        for n, text in lines:
            print(f"  {DESIGN}:{n}  {text}")
    print()
    headings = uncited_subsections(design, ledger)
    print(f"== Section 4 subsections no ledger block cites, {len(headings)}")
    print()
    for heading in headings:
        print(f"  {DESIGN}:{heading[0]}  {heading[2]}")
    print()
    return 0


# --- sig ---------------------------------------------------------------------------------------


def show_signatures(repo, names):
    status = 0
    include_private = "--all" in names
    roots = config(repo)["source_roots"]
    sources = source_files(repo)
    # The kit's and the project's own tools are code an agent calls too.
    sources += [name for name in tracked(repo, "tools/") if Path(name).suffix in docs_sig.ADAPTERS
                and name not in sources]
    for name in [name for name in names if name != "--all"]:
        name, _, member = name.partition(":")
        paths = docs_sig.find_sources(sources, name)
        if not paths:
            where = " or ".join(roots) if roots else "the tracked files"
            print(f'No source in a language sig reads is named "{name}" under {where}.')
            status = 1
            continue
        for path in paths:
            text = (Path(repo) / path).read_text(encoding="utf-8", errors="replace")
            if member:
                status |= show_member(path, text, member)
            else:
                print_signatures(path, text, include_private)
    return status


def show_member(path, text, member):
    """One member of a source file, whole, with line numbers: what to read before editing it."""
    lines = text.split("\n")
    ranges = docs_sig.member_ranges(path, text, member)
    stem = Path(path).stem
    if not ranges:
        print(f"{stem} declares no {member}. Its signatures: python tools/docs.py sig --all {stem}")
        return 1
    for first, last in ranges:
        print(f"== {stem}.{member}  {path}:{first}-{last}")
        for n in range(first, last + 1):
            print(f"{n:>5}  {lines[n - 1]}")
        print()
    return 0


def print_signatures(path, text, include_private):
    lines = text.count("\n") + 1
    print(f"== {Path(path).stem}  {path}  {lines} lines, ~{tokens(text):,} tokens whole")
    for n, depth, signature, summary in docs_sig.signatures(path, text, include_private):
        print(f":{n:<5}{'  ' * max(depth - 1, 0)}{signature}" + (f"  — {summary}" if summary else ""))
    print()


# --- project commands --------------------------------------------------------------------------

# tools/project_docs.py, when present, adds a project's own commands without editing this core file:
#     COMMANDS = {"kit": (handler, "    python tools/docs.py kit <name>    what the command prints")}
# where handler(repo, args) returns an exit code and args are the words after the command's name. Its
# usage text joins help in this file's format. It may also define problems(repo, files), returning
# (file, line, detail) tuples that check reports beside its own.

_plugins = {}


def plugin(repo=REPO):
    key = Path(repo).resolve()
    if key not in _plugins:
        path = key / PLUGIN
        module = None
        if path.is_file():
            spec = importlib.util.spec_from_file_location("project_docs", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        _plugins[key] = module
    return _plugins[key]


def project_commands(repo=REPO):
    module = plugin(repo)
    return getattr(module, "COMMANDS", {}) if module is not None else {}


def help_text(repo=REPO):
    usage = [entry[1].rstrip("\n") for entry in project_commands(repo).values()]
    if not usage:
        return __doc__
    return __doc__.rstrip("\n") + "\n\nThis project's own commands (tools/project_docs.py):\n\n" + "\n".join(usage) + "\n"


def help_for(words, text):
    """The usage entries whose command's first word is one of `words` (a command line and the lines under it,
    up to the next command or a blank line); for a word no command starts with, the entries mentioning it."""
    entries, current = [], None
    for line in text.splitlines():
        if line.startswith("    python tools/docs.py"):
            current = [line]
            entries.append(current)
        elif current is not None and line.startswith("    ") and line.strip():
            current.append(line)
        else:
            current = None
    chosen = []
    for word in words:
        first = [e for e in entries if e[0].split()[2:3] == [word]]
        chosen += [e for e in first or [e for e in entries if word in "\n".join(e)] if e not in chosen]
    return chosen


def show_help(words, repo=REPO):
    chosen = help_for(words, help_text(repo))
    if not chosen:
        print(f"No command or entry mentions {' '.join(words)}; python tools/docs.py help lists them all.")
        return 1
    for entry in chosen:
        print("\n".join(entry))
    return 0


# --- command -----------------------------------------------------------------------------------


def drop(files, args, repo=REPO):
    """drop q14 q9: removes open questions wherever they are asked; drop DESIGN.md "D. Offline mode": one heading."""
    if all(re.fullmatch(r"(?i)q\d+", arg) for arg in args):
        by_doc = {}
        for arg in args:
            home = question_home(repo, files, int(arg[1:]))
            if home is None:
                print(f"Question {arg[1:]} is not open in {DESIGN} 6.2 or a working document.")
                return 1
            by_doc.setdefault(home[0], []).append(int(arg[1:]))
        for name, numbers in by_doc.items():
            path = Path(repo) / name
            write(path, drop_questions(path.read_text(encoding="utf-8"), name, numbers))
            print(f"Dropped question{'s' if len(numbers) > 1 else ''} {', '.join(map(str, numbers))} from {name}.")
        print()
        report_empty_notes((Path(repo) / DESIGN).read_text(encoding="utf-8"))
        print()
        return check(files, repo)
    name = resolve_file(args[0], files)
    if name is None or len(args) < 2:
        print('drop takes question numbers (drop q14 q9) or a document and one heading (drop DESIGN.md "D. Offline mode").')
        return 1
    path = Path(repo) / name
    try:
        text, heading = drop_heading(path.read_text(encoding="utf-8"), name, " ".join(args[1:]))
    except ValueError as error:
        print(error)
        return 1
    write(path, text)
    print(f'Dropped "{heading}" and its block from {name}.')
    print()
    return check(files, repo)


def options_from(args, names):
    """(the arguments that are not options, {option: value}) for the --options in names, each taking a value."""
    rest, options = [], {}
    n = 0
    while n < len(args):
        if args[n] in names and n + 1 < len(args):
            options[args[n]] = args[n + 1]
            n += 2
        else:
            rest.append(args[n])
            n += 1
    return rest, options


def main(args, repo=REPO):
    global grep_window
    if len(args) >= 2 and args[0] == "help":
        return show_help(args[1:], repo)
    if not args or args[0] in ("-h", "--help", "help"):
        print(help_text(repo))
        return 0 if args else 1
    if "--full" in args:
        args = [arg for arg in args if arg != "--full"]
        grep_window = None
    repo = Path(repo)
    ids = ids_for(repo)
    files = tracked_markdown(repo)
    target = args[0]
    whole = " ".join(args).strip()
    today = str(datetime.date.today())

    extra = project_commands(repo)
    if target in extra:
        return extra[target][0](repo, args[1:])

    if target == "check":
        return check(files, repo)
    if target == "budget":
        return show_budgets(repo, files)
    if target == "context" and len(args) == 1:
        return show_context(repo)
    if target == "tail" and len(args) in (2, 3) and (len(args) == 2 or args[2].isdigit()):
        name = resolve_file(args[1], files)
        if name is None:
            print(f'No tracked document is named "{args[1]}".')
            return 1
        return show_tail(load(name, repo), int(args[2]) if len(args) == 3 else 3)
    if target == "toc" and len(args) == 2:
        name = resolve_file(args[1], files)
        if name is None:
            print(f'No tracked document is named "{args[1]}".')
            return 1
        print("\n".join(expected_contents(load(name, repo))))
        return 0
    if target == "outline" and len(args) == 2:
        if args[1].endswith(".py") and (repo / args[1]).is_file():
            return python_outline(repo / args[1], repo)
        name = resolve_file(args[1], files)
        if name is None:
            print(f'No tracked document is named "{args[1]}".')
            return 1
        return outline(load(name, repo))
    if target == "ledger" and args[1:2] not in (["insert"], ["replace"]):
        ledger = load_ledger(repo)
        print_block(ledger.doc, 1, ledger.ledger_end, "The ledger")
        return 0
    if target == "status" and len(args) >= 3 and ids.parse(args[1]):
        package_id = ids.parse(args[1])
        path = repo / LEDGER
        status = " ".join(args[2:])
        try:
            write(path, set_status(path.read_text(encoding="utf-8"), package_id, status, ids))
        except ValueError as error:
            print(error)
            return 1
        print(f"{package_id} — {status}")
        return check(files, repo)
    if target == "close" and len(args) >= 2 and ids.parse(args[1]):
        rest, options = options_from(args[2:], ("--steps", "--date", "--delivered"))
        if rest:
            print(f"close takes --steps N, --date YYYY-MM-DD and --delivered TEXT, not {' '.join(rest)}.")
            return 1
        try:
            done = close_package(repo, ids.parse(args[1]), options.get("--date", today),
                                 options.get("--steps"), options.get("--delivered"))
        except ValueError as error:
            print(error)
            return 1
        print("\n".join(done))
        print()
        return check(files, repo)
    if target == "close-initiative" and len(args) >= 2:
        rest, options = options_from(args[1:], ("--date",))
        ledger = load_ledger(repo)
        name = ledger.initiative_name(" ".join(rest))
        if name is None:
            print(f'"{" ".join(rest)}" is no Initiative. Initiatives: {", ".join(ledger.initiatives) or "none"}.')
            return 1
        try:
            done = close_initiative(repo, name, options.get("--date", today), files + tracked(repo, "tools/*.py"))
        except ValueError as error:
            print(error)
            return 1
        print("\n".join(done))
        print()
        return check(files, repo)
    if target == "drop" and len(args) >= 2:
        return drop(files, args[1:], repo)
    if target == "decisions" and len(args) >= 2 and (args[1:] == ["--all"] or all(
            re.fullmatch(r"(?i)q?\d+", arg) for arg in args[1:])):
        numbers = None if args[1] == "--all" else [int(arg.lstrip("qQ")) for arg in args[1:]]
        return show_decisions(repo, files, numbers)
    if target == "orphans" and len(args) == 1:
        return show_orphans(load(DESIGN, repo), load_ledger(repo))
    if target == "history" and len(args) == 3 and args[1] == "add":
        source = Path(args[2])
        if not source.is_file():
            print(f"{args[2]} is not a file.")
            return 1
        rows = [line.strip() for line in source.read_text(encoding="utf-8").split("\n") if line.strip()]
        problems = history_problems(rows)
        if not rows or problems:
            print("\n".join(f"row {n}: {detail}" for n, detail in problems) or f"{args[2]} holds no rows.")
            print(f"Nothing was written to {HISTORY}.")
            return 1
        path = repo / HISTORY
        try:
            write(path, append_history(path.read_text(encoding="utf-8"), rows))
        except ValueError as error:
            print(error)
            return 1
        print(f"Added {len(rows)} row{'s' if len(rows) > 1 else ''} to {HISTORY}.")
        print()
        return check(files, repo)
    if target == "ledger" and len(args) in (4, 5) and args[1] in ("insert", "replace"):
        path = repo / LEDGER
        try:
            if args[1] == "insert" and len(args) == 5 and args[3] == "--after" and ids.parse(args[4]):
                after = ids.parse(args[4])
                new = Path(args[2]).read_text(encoding="utf-8")
                write(path, insert_package(path.read_text(encoding="utf-8"), new, after, ids))
                print(f"Inserted the package after {after}.")
            elif args[1] == "replace" and len(args) == 4 and ids.parse(args[2]):
                package_id = ids.parse(args[2])
                new = Path(args[3]).read_text(encoding="utf-8")
                write(path, replace_package(path.read_text(encoding="utf-8"), package_id, new, ids))
                print(f"Replaced {package_id}.")
            else:
                print(f"ledger takes insert FILE --after {ids.prefix}-n, or replace {ids.prefix}-n FILE.")
                return 1
        except (ValueError, OSError) as error:
            print(error)
            return 1
        print()
        return check(files, repo)
    if target == "record":
        rest, options = options_from(args[1:], ("--date", "--by"))
        answers = {}
        for arg in rest:
            answer = re.fullmatch(r"(?is)q?(\d+)=(.+)", arg)
            if not answer:
                print(f'"{arg}" is neither --date, --by nor an answer such as 14=rec or "15=(b), because ...".')
                return 1
            answers[int(answer.group(1))] = answer.group(2).strip()
        try:
            done = record_answers(repo, files, options.get("--date", today),
                                  options.get("--by", config(repo)["owner"]), answers)
        except ValueError as error:
            print(error)
            return 1
        for line in done:
            print(line)
        print()
        return check(files, repo)
    if (target == "raise" and len(args) == 2) or (target == "round" and len(args) == 3 and args[1] == "add"):
        source = Path(args[-1])
        if not source.is_file():
            print(f"{args[-1]} is not a file.")
            return 1
        try:
            done = add_draft(repo, source, target == "round")
        except ValueError as error:
            print(error)
            print("Nothing was written.")
            return 1
        print("\n".join(done))
        print()
        return check(files, repo)
    if target == "round" and (len(args) == 1 or (len(args) == 2 and args[1].isdigit())):
        text = chat_round(load(ROUNDS, repo), int(args[1]) if len(args) == 2 else None)
        if text is None:
            print(f"{ROUNDS} has no such round still asking a question.")
            return 1
        print(text)
        return 0

    package_id = ids.parse(target)
    if package_id and len(args) == 1:
        return show_package(load_ledger(repo), load(DESIGN, repo), package_id)

    question = re.fullmatch(r"(?i)(?:q|question\s*)(\d+)", whole)
    if question:
        found = question_home(repo, files, int(question.group(1)))
        if found is None:
            print(f"Question {question.group(1)} is not open in {DESIGN} 6.2 or a working document: answered and"
                  f" consolidated (its reason is in {HISTORY}), or never raised.")
            return 1
        print_block(load(found[0], repo), *found[1:], f"Question {question.group(1)}")
        return 0

    specs = section_specs(args)
    if specs:
        design = load(DESIGN, repo)
        missing = [number for number, _, _ in specs if find_section(design, number) is None]
        if missing:
            print(f"{DESIGN} has no section {', '.join(missing)}. Its outline: python tools/docs.py {DESIGN}")
            return 1
        for n, (number, own, pattern) in enumerate(specs):
            if n:
                print()
            show_section(design, find_section(design, number), own, pattern)
        note = unfiltered_note(specs)
        if note:
            print()
            print(note)
        return 0

    if target == "sig" and len(args) >= 2:
        return show_signatures(repo, args[1:])
    if target == "where" and len(args) >= 2:
        return show_where_all(load(WHERE, repo), args[1:])

    name = resolve_file(target, files)
    if name is not None:
        rest, pattern = grep_option(args[1:])
        query = " ".join(rest).strip()
        doc = load(name, repo)
        if pattern:
            if not query:
                print_grep(doc, 1, len(doc.lines), pattern, doc.name)
                return 0
            heading = [h for h in doc.headings if query.lower() in h[2].lower()]
            if len(heading) != 1:
                return show_heading(doc, query)
            print_grep(doc, *heading_block(doc, heading[0]), pattern, heading[0][2])
            return 0
        return outline(doc) if not query else show_heading(doc, query)
    if target.endswith(".md"):
        print(f'No tracked document is named "{target}".')
        return 1

    ledger = load_ledger(repo)
    initiative = ledger.initiative_name(whole)
    if initiative is not None:
        return show_initiative(ledger, initiative)
    print(f'"{whole}" is no package, section, question, document or Initiative.'
          f" Initiatives: {', '.join(ledger.initiatives) or 'none'}.")
    return 1


if __name__ == "__main__":
    # Documents hold arrows and other characters a Windows console code page cannot encode.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
