---
name: lg-package
description: Run Work Packages through their lifecycle — cut a Work-Ready Initiative into packages, build one (rules first, code, tests, manual check), close it on the owner's approval with its delivery record, close an Initiative when its last package lands, and run retros. Use whenever the task names a package id from LEDGER.md, says "build", "cut", "close" or "approve" about a package or Initiative, or asks for a retro.
argument-hint: "[XX-nnn | cut <Initiative> | close XX-nnn | retro]"
---

# lg-package

How a Work Package is cut, built and closed. `XX` stands for the project's package prefix (`tools/leanground.json`). This skill and the stage files beside it are the procedure's one home; `working-agreements.md` "Initiatives and Work Packages" holds the ledger's format, and `DESIGN.md` 6's opening (`python tools/docs.py 6 --own`) the concepts. **Docs, tooling, cleanups and fixes are just work: no package, no id, no ledger line.**

**Read a stage file only when you reach its stage:** `cut.md` (cut an Initiative), `build.md` (build and verify in this session), `dispatch.md` (a build sized for chunk subagents), `handover.md` (the manual check: read it before writing fixtures, which come before the first build), `close.md` (close a package or an Initiative), `retro.md` (only when the owner asks). A bracketed id names the incident behind a step, in `why.md`: read it only to challenge the step.

**Who decides.** The owner: moving an item between ledger groups, starting work, a cut's granularity, builder and reviewer per line, approving finished work, closing an Initiative. The agent makes those edits when told. Never infer a decision from approval of adjacent work or a passing build. **One package per session:** after a close, stop. Don't offer or ask about the next package, or bundle "and start XX-nnn" into a close-out.

## Ledger statuses

Written on the ledger line after the dash, and nowhere else:

- Initiative: `cut`, optionally `; questions N to M open, left for <collaborator>`
- Package: `can be built` · `waits on question N` · `waits on XX-nnn` (joined with "and") · `being built` · `built; awaiting the owner's check`

`python tools/docs.py status XX-nnn <status>` writes the line and runs the check. After any other `LEDGER.md` edit: `python tools/docs.py check`.

## Build a package

Precondition: its line says `can be built` and the owner said to start.

1. **Read:** `python tools/docs.py XX-nnn` (line, block, questions, a menu of cited sections and packages), with `where <system>` and `tail design-history.md 1` in the same call. Confirm the block has every field `cut.md` lists and no open question changes its scope; if one does, stop and say so. Then read only what the work needs, in as few calls as you can (each is a turn):
   - **Design:** a short section whole; a long one (over ~1,500 tokens on the menu) as its own text and the subsection needed, or only the lines that matter: `python tools/docs.py 4.3 --own 4.3.2 --grep "cache|retry"`.
   - **Where code lives:** `where "recipe: <kind>"` lists the files a common addition touches, in order. Use a recipe, never a past package's diff [AZ-141].
   - **Code you only call:** `python tools/docs.py sig <Name> …`, several in one call; never Read it.
2. **Size it before reading code,** from the block alone: the files its Touches and recipes name. Under about 20 files this session builds it (`build.md`) [PF-539]. Past that, tally the plan's lines by `dispatch.md` section 1: one chunk is still built here; more makes this session the manager.
3. **Locate the seams.** With about twelve or fewer source files naming them, or a predecessor commit in the same family (`git show --stat --format= <sha>` is the site list, whole), locate them inline in one batch of searches, names matched at word boundaries [PF-523, PF-540, PF-531]. Beyond that, one read-only `Explore` subagent with a hard stop: briefed with the block's Outcome and Done when, the facts already decided and the ground it owns; 20 calls, then it reports what it has and names what it did not reach; at most 350 words, each `file:line` one it opened with a few words quoted; no predictions, fixes or file dumps [PF-533]. `model: "haiku"` returns sites only; mapping rows to fields or answering "is there an X" takes `"sonnet"`, and its "none found" is checked before it shapes a decision [PF-633]. Check every count and absence you rely on yourself [PF-520].
   - **For chunks,** write each seam as name and `file:line`, tagged with the chunks that need it, and print only a signature the plan's text depends on, never a body: each chunk reads it again [PF-539]. Never print a window over about 40 lines to orient [PF-542].
4. **Start; the rules first.** Make the package's rules exact in the system's **Built rules** subsection of `DESIGN.md` section 4 (and section 7 if it has a cost), with a history row `| date | XX-nnn Name, the rules (sections): <the rules> | <why; the builder's choices> |` written to a scratch file and added by `python tools/docs.py history add <file>`; then `python tools/docs.py status XX-nnn being built`, whose check needs that row. A new heading gets its Contents line (`toc DESIGN.md`). Work out a table's numbers before writing it in; a timed rule names its hold control (`handover.md` pass 1). Rules that hang on a tool's verdict: write and run the tool first; only the commits' order is fixed [AZ-145]. A fork the block leaves open: a design choice is raised as a question (the lg-design skill) and stops the build if it changes scope; a builder's choice is decided, written into the rules and the row's reason, and listed under the handover's "Defaults I chose".
   **Attack the exact text** before any plan: one read-only Agent call, `model: "sonnet"`, given the rule text and the systems it meets: "List the situations this text leaves undecided or decides two ways, at most 200 words, no fixes, [T] where two readings make tests assert different outcomes; check every other writer of the state it writes, the acting entity's own case, its arithmetic, and older design sentences it contradicts." Decide each [T] in the rules; each exclusion the rules name gets its own red test [PF-537, PF-614, PF-622]. Check and commit only if the check passes: `XX-nnn Name: start building; the rules`.
5. **Baseline, then build.** Before the first edit, run the slow tests the predecessor named (else this block's), fail-fast off, editing nothing they serve meanwhile; "it predates this change" needs a red run at the parent commit [PF-519, PF-576, PF-528]. Then `build.md` in this session, or `dispatch.md` as the manager. Both end at `handover.md`.

## Throughout

- One line to the owner at each stage's start: reading done, rules committed, build running, fixtures written.
- Search and read tracked files with Grep, `git grep`, Read and `tools/docs.py`; the hooks refuse the shell's readers and shell edits. Whether something is planned: `git grep -n -i <word> -- LEDGER.md`.
- A lesson waits in `docs/agent-notes/lessons.md` for a retro (`close.md` step 3); a package session changes no skill, note or tool for it, unless it blocks the package under way.
- Design choices found while cutting or building go into `DESIGN.md` 6.2 as numbered questions (the lg-design skill), never asked in chat; loose ends not fixed go into 6.7 with "Found in XX-nnn".
