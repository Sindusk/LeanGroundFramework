---
name: package
description: Run Work Packages through their lifecycle — cut a Work-Ready Initiative into packages, build one (rules first, code, tests, manual check), close it on the owner's approval with its delivery record, close an Initiative when its last package lands, and run retros. Use whenever the task names a package id from LEDGER.md, says "build", "cut", "close" or "approve" about a package or Initiative, asks for a retro, or edits LEDGER.md.
argument-hint: "[XX-nnn | cut <Initiative> | close XX-nnn | retro]"
---

# package

How a Work Package is cut, built and closed. `XX` stands for the project's package prefix (`tools/leanground.json`). This skill and the stage files beside it are the procedure's one home; `working-agreements.md` "Initiatives and Work Packages" holds the ledger's format, and `DESIGN.md` 6's opening (`python tools/docs.py 6 --own`) the concepts. **Docs, tooling, cleanups and fixes are just work: no package, no id, no ledger line.**

**Read a stage file only when you reach its stage:** `cut.md` (cut an Initiative), `dispatch.md` (a build too large for one context), `handover.md` (the manual check: read it before writing fixtures, which come before the first build), `close.md` (close a package or an Initiative), `retro.md` (only when the owner asks). A bracketed id names the incident behind a step, in `why.md`: read it only to challenge the step.

**Who decides.** The owner: moving an item between ledger groups, starting work, a cut's granularity, builder and reviewer per line, approving finished work, closing an Initiative. The agent makes those edits when told. Never infer a decision from approval of adjacent work or a passing build. **One package per session:** after a close, stop. Don't offer or ask about the next package, or bundle "and start XX-nnn" into a close-out.

## Ledger statuses

Written on the ledger line after the dash, and nowhere else:

- Initiative: `cut`, optionally `; questions N to M open, left for <collaborator>`
- Package: `can be built` · `waits on question N` · `waits on XX-nnn` (joined with "and") · `being built` · `built; awaiting the owner's check`

`python tools/docs.py status XX-nnn <status>` writes the line and runs the check. After any other `LEDGER.md` edit: `python tools/docs.py check`.

## Build a package

Precondition: its line says `can be built` and the owner said to start.

1. **Read:** `python tools/docs.py XX-nnn` (line, block, questions, a menu of cited sections and packages), with `where <system>`, `sig` for its Touches and `tail design-history.md 1` in the same call. Confirm the block has every field `cut.md` lists and no open question changes its scope; if one does, stop and say so. Then read only what the work needs, gathering lookups into as few calls as you can, since each call is a turn:
   - **Design:** a short section whole; a long one (over ~1,500 tokens on the menu) as its own text and the subsection needed, or only the lines that matter: `python tools/docs.py 4.3 --own 4.3.2 --grep "cache|retry"`.
   - **Where code lives:** `python tools/docs.py where <system>`; `where "recipe: <kind>"` lists the files a common addition touches, in order. Use a recipe, never a past package's diff [AZ-141].
   - **Code you only call:** `python tools/docs.py sig <Name> …`, several in one call; never Read it. **A sibling to copy:** Read it whole; `sig` the rest.
   - **Code you will edit:** whole when short (under ~150 lines) or changed throughout; otherwise `sig`, then its imports and the ranges you change (`sig Name:member` prints one member with line numbers).
   - **The seam map:** a lookup needing more than one Grep (every caller of a changed API) goes to one Explore agent with `model: "haiku"`, for sites as `file:line`, never judgements.
2. **Start; the rules first.** Make the package's rules exact in the system's **Built rules** subsection of `DESIGN.md` section 4 (and section 7 if it has a cost), with a history row `| date | XX-nnn Name, the rules (sections): <the rules> | <why; the builder's choices> |` written to a scratch file and added by `python tools/docs.py history add <file>`; then `python tools/docs.py status XX-nnn being built`, whose check needs that row. A new heading gets its Contents line (`toc DESIGN.md`). Work out a table's numbers before writing it in. A fork the block leaves open: a design choice is raised as a question (the design skill) and stops the build if it changes scope; a builder's choice is decided, written into the rules and the row's reason, and listed in the handover under "Defaults I chose". Check and commit only if the check passes: `XX-nnn Name: start building; the rules`.
   **Then `python tools/docs.py context`.** Past the threshold it prints, or when the plan spans more than about 20 files, the build goes to subagents: `dispatch.md`.
3. **Build** in logical commits, each `XX-nnn Name: <what it does>`.
   - **Declare before use:** new types first, then the members others call, then their callers; imports in the same edit as their first use.
   - Batch independent edits into one turn: every turn resends the conversation.
   - **Changing a signature others call:** add the new form beside the old, move every caller in one turn, then remove the old.
   - **Test expectations:** work each expected value out by hand first, checking for exact divisions and rounding that would make a case pass trivially.
   - When code makes a Built rule false, update the rule in the same change.
   - **Check each novel seam the block plans is needed** against what already holds the data [AZ-141].
   - **Unexpected scope:** what the outcome needs stays in; a useful extension becomes a peer package offered to the owner; a discovery that breaks the boundary means stop and re-plan openly.
4. **Verify** with the commands in `working-agreements.md` "Build and verify", run quietly and filtered to their pass and fail lines. Write tests for every behaviour a test can reach; a scheduled or timed thing exposes its step as a method returning what it did, so a test calls it directly. **Falsify the package's two or three key tests:** break the code each pins, watch it fail, undo the break with Edit; a test that stays green gets one more case, else say it is unproven. Two to five per package, not per chunk [PF-541]. Write the manual check's fixtures before the first build (`handover.md`), so one build covers everything.
5. **Handover:** `handover.md`. A package with nothing a test can't show still sets `built; awaiting the owner's check` and reports what to review.
6. Loose ends not fixed go into `DESIGN.md` 6.7 with "Found in XX-nnn".

## Throughout

- One line to the owner at each stage's start: reading done, rules committed, build running, fixtures written.
- Search and read tracked files with Grep, `git grep`, Read and `tools/docs.py`; the hooks refuse the shell's readers and shell edits. Whether something is planned: `git grep -n -i <word> -- LEDGER.md`.
- A lesson waits in `docs/agent-notes/lessons.md` for a retro (`close.md` step 3); a package session changes no skill, note or tool for it, unless it blocks the package under way.
- Design choices found while cutting or building go into `DESIGN.md` 6.2 as numbered questions (the design skill), never asked in chat.
