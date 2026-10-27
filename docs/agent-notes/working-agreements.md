# Working agreements

How work runs in this repository. `CLAUDE.md` routes here; read the section your task needs, not the whole file. Design rules live in `DESIGN.md`, never here.

## Initiatives and Work Packages

`DESIGN.md` section 6 is the roadmap and defines the concepts (Initiative, Work Package, just work, Release); read its opening (`python tools/docs.py 6 --own`), not all of it. This section is how they are operated. **Do not mint a package for ordinary work**: docs, tooling, cleanups and fixes are just work, with no ID and no ledger line.

- **The ledger** (`LEDGER.md` at the root) is one line per item, grouped Work-Ready, Designed, Undesigned, as `- **Name** — where it stands`, with an indented `{{PREFIX}}-` line for each package an Initiative owns and an indented path to the file its design is worked out in. The owner reads it as raw text: no tables, no links, no detail on the lines (its Contents section is the one place links are allowed). Details live in the item's block under the Initiatives heading below the ledger, a `### Name` heading matching its ledger name, with each package as a `- **{{PREFIX}}-n Name.**` item in its Initiative's block. A standalone package is an unindented `- {{PREFIX}}-n Name (builder) — where it stands` line in its group, with its block under `### Standalone Work Packages`. Where an item stands is written on its ledger line and nowhere else: no heading, block, commit subject or note repeats it. `python tools/docs.py check` enforces the format, the pairing of lines and blocks, and the next free ID; run it after every ledger edit.
- **Who decides what.** The agent keeps the words after the dash true as work proceeds. Moving an item between groups, starting work on a Work-Ready item, approving finished work (which removes it from the ledger and writes its delivery record) and marking a Release done are the owner's decisions; the agent makes the edit when told. Don't infer a decision from approval of adjacent work or a passing build.
- **Cutting, building and closing** a package or Initiative are the package skill's: `.claude/skills/package/`.
- **Claiming an ID.** The ledger is the only allocator: an ID exists once a line carrying it is committed; the ledger states the next free number; retired numbers are never reused.
- **Builders and reviews.** Each package line names its builder by exact model name, "(Claude Opus 5.5)". The owner decides per Initiative or package whether a line also names a reviewer, "(Claude Sonnet 5.5, reviewed by Claude Opus 5.5)"; a build is never reviewed by its own model.
- **Naming.** A package's commit subject leads with its ID and name ("{{PREFIX}}-104 Search filters: …"); ordinary work uses an ordinary subject.
- **Delivery records** go into `docs/archive/initiatives/` when a package closes, one file per Initiative with one block per package (naming in `docs/archive/README.md`), and never live in `DESIGN.md`.

## Design changes

- **Design first.** Behaviour is written into `DESIGN.md` and reviewed by the owner before any code. Implement from the design only; there are no per-module specs.
- **Where design work happens.** A new question starts as a numbered item in `DESIGN.md` 6.2, which explains how a question runs. When an Initiative's design outgrows a few questions it gets one working document in `docs/initiatives/`, named for the Initiative and headed "working document, not authority"; its ledger line gets the path. Each accepted decision is consolidated into `DESIGN.md` (the rule) and `design-history.md` (the reason) when the owner asks. When the Initiative closes, its working document moves unedited to `docs/archive/initiatives/`, beside its record.
- **Put only real choices to the owner,** each with a recommendation, the tradeoff and the cost of being wrong, numbered so they can answer by number. Decide routine details in the document and say so.
- **Batched design rounds go in `design-questions.md`** at the root, in its Explanation / Gap / Options / Recommendation / Response format, written for a reader outside the project.
- **Every behaviour change to `DESIGN.md` gets a dated row in `design-history.md`** and the owner's review before committing. Formatting-only fixes need neither. A change the owner asked for in so many words counts as reviewed once they have seen the result.
- **A built system's rules live in its Built rules subsection** of `DESIGN.md` section 4. **Update them in the same change when code makes them false**: a small refinement found while building is edited in place; a behaviour change also gets a history row.
- **Rule text states the present rule.** No "used to" or "no longer" in `DESIGN.md`; history belongs in `design-history.md` and git. Facts that change with the code (counts, file lists, versions) are read from the code, not copied into prose.

## Open questions and loose ends

- **Open design questions live in `DESIGN.md` 6.2**, with the idea backlog, under permanent numbers that other documents cite (the next free number is stated there). A question that is answered is removed at consolidation, not struck through; git keeps its text. Never renumber the rest. Numeric tuning questions live in `DESIGN.md` section 11.
- **Record questions, don't ask them in chat.** A design choice found during any work is written into 6.2 as a numbered question and cited from the design text and ledger lines; the reply only points at the numbers. A design round is the exception: once written, its questions are put to the owner in chat (the design skill). Otherwise only non-design housekeeping, such as whether to delete a file, is asked in chat.
- **Questions may be left for a collaborator** named in `tools/baseline.json`, who answers with their own agent. When the owner says so, leave the questions open and record no decision, say so in a note in 6.2 and as "left for <name>" on the Initiative's ledger line, and write each question to stand alone (gap, candidates, recommendation, cost of being wrong) for an agent reading it cold.
- **Known issues live in `DESIGN.md` 6.7**, not in session handoffs. When a session finds a loose end it is not fixing (documentation that disagrees with the code, a TODO, a harmless warning, a check not yet done), add it there. When one is fixed, remove its line.

## Writing documents

- **Leave a blank line between a bold label and the list under it.** Otherwise a numbered list not starting at `1.` renders as one run-on line on GitHub.
- **A `## Contents` section matches its document's headings,** `##` to `####`, as linked bullets. `DESIGN.md` and `LEDGER.md` have one. After adding, renaming or removing a heading there, replace the section with the output of `python tools/docs.py toc <file>`; `check` reports one that has gone stale.
- **A list whose numbers are cited elsewhere uses bold numbers in bullets** (`- **11.** ...`), not a Markdown ordered list, so removing an item never renumbers the rest.
- **Write for the owner in their terms,** not internal identifiers: what a user sees and does, then the id in brackets if it helps.
- **Grids, layouts and tables of slots** go in a code block, one bracketed cell per slot (`[Glow]`, `[    ]` for empty), plus a short key; never as strings whose spaces carry meaning.
<!-- bootstrap: the project's own document conventions, if any. -->

## Shell and editing

- Edit existing files with the Edit tool and create new ones with Write. Never write files through the shell; a hook blocks it.
- Search tracked files with the Grep tool or `git grep`, and read them with Read (a range) or `python tools/docs.py`; a hook refuses the shell's readers on tracked files. Logs and build output may use the shell.
- Several patterns: `git grep -e 'a' -e 'b'`, single-quoted.
<!-- bootstrap: the primary shell and its traps. For Windows PowerShell 5.1: no redirects (a hook blocks them, `2>$null` too); keep `>` and double quotes out of commit messages, since PowerShell splits a here-string at them when passing it to git; "LF will be replaced by CRLF" warnings are harmless. -->

## Build and verify

<!-- bootstrap: each command from tools/baseline.json "commands", one bullet each: what it runs, how long it takes, how to read its result quietly (a filter that prints only the pass/fail lines), and where the full log is. Then the test layers: what a unit test covers, what an integration or end-to-end test covers, where each lives, and what must never be faked. -->
- `python tools/docs.py check`: every design section cited in the live documents and sources resolves, the ledger agrees with its blocks, every question a line names exists, no example names a real package id (write `{{PREFIX}}-nnn`), and each file an agent loads unasked is within its token budget (`python tools/docs.py budget`). Run it after changing section numbers, the ledger, a package block, `CLAUDE.md` or a skill. `python -m unittest tools/test_docs.py` tests the script; run it after changing `tools/docs.py`.

## Manual checks

What a test can't show (look, feel, layout, sound, a real device, a third-party service) is checked by the owner from a checklist the package skill's `handover.md` writes. A launch of the app for a manual check always waits for the owner's go-ahead, and so does a relaunch.
<!-- bootstrap: how the owner runs the app for a check (the run command, a fixture or seed that sets up the state a checklist needs, debug controls), and whether a dev server they keep running should be reused rather than started. -->

## Commits and handoffs

- Committing, pushing and the commit trailer follow `CLAUDE.md`'s "Commits". Earlier commits are left as they are.
- **Several agents in one checkout:** `git add` only your own paths, never `-A`; never stash, reset or switch branch; don't fix errors in files another agent is changing.
- **Public repository:** before committing anything that may be sensitive (a host, a login, a key, personal data, a third party's file), offer the owner redaction, a gitignore entry or committing as is.
- A handoff states what was done, what is not done, and what the owner should check. Loose ends go into `DESIGN.md` 6.7, not into the handoff alone.

## Skills and agents

- **A skill** is `.claude/skills/<name>/SKILL.md` with `name`, a `description` (what it does, then "Use when …" with the words that should trigger it) and, if it takes one, an `argument-hint`. Its body is a router: the steps every run needs, then which stage file to read at which stage. Stage files sit beside it and are read only at their stage.
- **Rules, not stories.** A rule learned from an incident carries the package id in brackets (`[{{PREFIX}}-nnn]`); the story, if worth keeping, goes in the skill's `why.md`, which is read only to challenge a rule.
- **Budgets.** Every file an agent loads unasked (`CLAUDE.md`, skill files, agent definitions, skill descriptions) has a token budget in `tools/baseline.json`, checked by `check`. Trim before raising one; a raise states its reason in the commit body.
- **Prefer a tool to prose.** A step an agent does the same way every time becomes a `tools/docs.py` command, a hook or a script bundled with its skill in `.claude/skills/<name>/tools/`: deterministic, read-only unless named otherwise, with a header comment giving its purpose and exact usage. A tool that condenses a large input audits its own losses.
- **Subagents** are briefed with the `docs.py` commands they need and the `file:line` sites already found, not files to read, and return a short report in a fixed shape.

## Owner preferences

How the owner likes to work, learned from real corrections. Each is a bold rule, then "(owner, date)" and, if useful, what prompted it. A preference that applies to every task moves to `CLAUDE.md` "Always".

<!-- bootstrap: any preferences the owner states in the interview; else "None recorded yet." -->
