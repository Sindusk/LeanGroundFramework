---
name: lg-package
description: Run Work Packages through their lifecycle — cut a Work-Ready Initiative into packages, build one (rules first, code, tests, manual check), close it on the owner's approval with its delivery record, close an Initiative when its last package lands, and run retros. Use whenever the task names a package id from LEDGER.md, says "build", "cut", "close" or "approve" about a package or Initiative, or asks for a retro.
argument-hint: "[XX-nnn | cut <Initiative> | close XX-nnn | retro]"
---

# lg-package

How a Work Package is cut, built and closed. `XX` stands for the project's package prefix (`tools/leanground.json`). The procedure lives only here; the ledger's format is in `working-agreements.md` "Initiatives and Work Packages", the concepts in `DESIGN.md` 6's opening (`python tools/docs.py 6 --own`). **Docs, tooling, cleanups and fixes are just work: no package, no id, no ledger line.**

**Read a stage file only when you reach its stage:** `cut.md` (cut an Initiative), `build.md` (build and verify in this session), `dispatch.md` (a build sized for chunk subagents), `handover.md` (the manual check: read it before writing fixtures, which come before the first build), `close.md` (close a package or an Initiative), `retro.md` (only when the owner asks). A bracketed id names the incident behind a step, in `why.md`: read it only to challenge the step.

**Who decides.** The owner: moving an item between ledger groups, starting work, a cut's granularity, builder and reviewer per line, approving finished work, closing an Initiative. The agent makes those edits when told. Never infer a decision from approval of adjacent work or a passing build. Where the package print ends `close: on_build`, "build XX-nnn" is also the approval to close it (`close.md`). **One package per session:** after a close, stop. Never offer, ask about or bundle in the next package.

## Ledger statuses

On the ledger line after the dash, nowhere else:

- Initiative: `cut`, optionally `; questions N to M open, left for <collaborator>`
- Package: `can be built` · `waits on question N` · `waits on XX-nnn` (joined with "and") · `being built` · `built; awaiting the owner's check`

`python tools/docs.py status XX-nnn <status>` writes the line and runs the check. After any other `LEDGER.md` edit: `python tools/docs.py check`.

## Build a package

Precondition: its line says `can be built` and the owner said to start.

1. **Read:** `python tools/docs.py XX-nnn` (block, questions, a menu of its citations), with `where <system>` and `tail design-history.md 1` in the same call. Confirm the block has every field `cut.md` lists and no open question changes its scope; if one does, stop and say so. Then read only what the work needs, in as few calls as you can:
   - **Design:** a short section whole; a long one (over ~1,500 tokens on the menu) as its own text and the subsection needed, or only the lines that matter: `python tools/docs.py 4.3 --own 4.3.2 --grep "cache|retry"`.
   - **Where code lives:** `where "recipe: <kind>"` lists the files a common addition touches, in order. Use a recipe, never a past package's diff [AZ-141].
   - **Code you only call:** `python tools/docs.py sig <Name> …`, several in one call; never Read it.
2. **Size it before reading code,** from the block alone: the files its Touches and recipes name. Under about 20 files this session builds it (`build.md`) [PF-539]. Past that, tally the plan's lines by `dispatch.md` section 1: one chunk is still built here; more makes this session the manager.
3. **Locate the seams.** With about twelve or fewer source files naming them, or a predecessor commit in the same family (`git show --stat --format= <sha>` is the site list, whole), locate them inline in one batch of searches, names matched at word boundaries [PF-523, PF-540, PF-531]. Beyond that, one read-only `Explore` subagent with a hard stop: briefed with the block's Outcome and Done when, the facts decided and its ground; at 20 calls it reports what it has and what it did not reach, in at most 350 words, each `file:line` one it opened, quoted in a few words, with no predictions, fixes or file dumps [PF-533]. `model: "haiku"` returns sites only; mapping rows to fields or answering "is there an X" takes `"sonnet"`, whose "none found" is checked before it shapes a decision [PF-633]. Check every count and absence you rely on yourself [PF-520].
   - **For chunks,** write each seam as a plan row (`dispatch.md` section 1) and print only a signature the plan's text depends on, never a body: each chunk reads it again [PF-539]. Never print a window over about 40 lines to orient [PF-542].
4. **Start; the rules first.** Make the package's rules exact in the system's **Built rules** subsection of `DESIGN.md` section 4 (and section 7 if it has a cost), with a history row `| date | XX-nnn Name, the rules (sections): <the rules> | <why; the builder's choices> |` added from a scratch file by `python tools/docs.py history add <file>`; then `python tools/docs.py status XX-nnn being built`, whose check needs that row. A new heading gets its Contents line (`toc DESIGN.md`). Work out a table's numbers before writing it in; a timed rule names its hold control (`handover.md` pass 1). Rules that hang on a tool's verdict: write and run the tool first; only the commits' order is fixed [AZ-145]. Start the note, `python tools/docs.py note XX-nnn`, adding each ruling, default, unbuilt item and lesson as it arises. A fork the block leaves open: a design choice is raised as a question (the lg-design skill) and stops the build if it changes scope; a builder's choice is decided, written into the rules and the row's reason, and noted as a default with its alternatives. With `forks: decide` on the package print, so is a fork whose answers cost differently (on the recommendation) and the re-cut of a package found oversized (halves at a seam, new ids), the report leading with the defaults; ask only where no recommendation is defensible or an action needs approval [PF split rulings 2026-11-15].
   **Attack the exact text** before any plan: one read-only Agent call, `model: "sonnet"`, given the rule text and the systems it meets: "List the situations this text leaves undecided or decides two ways, at most 200 words, no fixes, [T] where two readings make tests assert different outcomes; check every other writer of the state it writes, the acting entity's own case, its arithmetic, and older design sentences it contradicts." Decide each [T] in the rules; each exclusion the rules name gets its own red test [PF-537, PF-614, PF-622]. Check and commit only if the check passes: `XX-nnn Name: start building; the rules`.
5. **Baseline, then build.** Before the first edit, run the slow tests the predecessor named (else this block's), fail-fast off, editing nothing they serve meanwhile; "it predates this change" needs a red run at the parent commit [PF-519, PF-576, PF-528]. Then `build.md` in this session, or `dispatch.md` as the manager. Both end at `handover.md`.

## Throughout

- One line to the owner as each stage starts.
- The hooks refuse the shell's readers and edits: use Grep, `git grep`, Read and `tools/docs.py`. Whether something is planned: `git grep -n -i <word> -- LEDGER.md`.
- A lesson ("<what cost turns, with a count> → <the change>", at most three) goes in the note for the close to queue; a package session changes no skill, note or tool for it, unless it blocks the package under way.
- Design choices found while cutting or building go into `DESIGN.md` 6.2 as numbered questions (the lg-design skill), never asked in chat; loose ends not fixed go into 6.7 with "Found in XX-nnn".
