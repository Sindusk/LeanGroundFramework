---
name: feedback
description: A polish pass over the owner's loose notes — a pasted list of things to change, review notes, "some things I noticed" — worked outside any Work Package. Triage each note by size, ask the owner once, send small mechanical items to fix subagents, build the rest inline, verify once for the whole pass, commit. Use whenever the owner hands over a list of feedback, notes or polish items, even when the request never says "feedback".
argument-hint: "[the notes, pasted]"
---

# feedback

A pass is a list of the owner's notes, each a small user-facing change, with no package id (`working-agreements.md`: a package only for an Initiative's component). `CLAUDE.md` binds every step.

**Why the shape is this one.** A pass spends its tokens finding code, seeing each change run, and on defects found late (a layering rule broken, an earlier ruling undone). Subagents repay only where an item is small and self-contained; one per item repays the search twice and multiplies verification. So triage is one read-only sweep, verification is once per pass, and only the mechanical items leave the session.

## 1. Triage, read-only

For each note, in one sweep (batch searches; `python tools/docs.py sig <name>` for a declaration; `git grep` a visible string or test id to find a screen):

- **Where it lives:** the files it edits and the tests that pin them.
- **What it overturns:** `git log -S` on the thing being removed or moved, and the design text that states it (`python tools/docs.py DESIGN.md --grep <words>`). A note that reverses an earlier ruling is still built (the newer word wins), but the ruling's purpose is checked against the new build.
- **What it crosses:** a layering rule (`DESIGN.md` 3), stored data or its schema, a performance rule (section 7).
- **Size:**
  - **S:** one to three files, no new component, no design judgment, nothing the owner must see before it is right: a rename, a placement, copy.
  - **M:** a new component or a data join, or a layout the owner will judge.
  - **L:** touches rules, stored data, or more than one screen's structure. An L is offered to the owner as a package for the ledger rather than built in a pass, unless they say build it.

Tell the owner the size of the pass before building, one line per note: `<note> — <S/M/L> — <files> — <route>`.

## 2. Questions, once

Every fork goes in one AskUserQuestion before building, options with the recommendation first, framed as what the user sees. A look the owner must judge (a placement, a width, a colour) is not asked in prose: build the recommendation, show the alternatives, and put the choice first in the handoff. Edge cases are not asked: take the recommendation and list it under "Defaults I chose".

## 3. Build

- **S items go to `fix` subagents** (`.claude/agents/fix.md`, Sonnet). Write each brief to `working/pending/feedback-<date>/<n>-brief.md` (gitignored) in the template below, then dispatch with Agent, `subagent_type: "fix"`, the prompt carrying only the brief's path. Up to three run at once, only when their Files lists are disjoint.
- **M and accepted L items are built inline**, while the subagents run.
- **The design and other shared prose have one writer: this session.** A brief never lists `DESIGN.md` or `docs/`; write each change's design text yourself, and a behaviour change gets its history row (`python tools/docs.py history add`).

```markdown
# Feedback <date> item <n> brief
## The note
<the owner's words, verbatim>
## The change
<what to build, with exact values and ids; the owner's ruling if asked>
## Files
<each file to edit, with the sibling it copies or the function it joins>
## Tests
<the test file to extend or add, and what it asserts; tests pinning the old behaviour, by file:line>
## Not yours
DESIGN.md, docs/, every file another item lists, and anything git status shows you did not write.
```

Read each report when it arrives; check `git diff --stat` against its Files. A defect goes back to the same subagent with SendMessage while it is small.

## 4. Verify once, for the whole pass

`working-agreements.md` "Build and verify" holds. In order, each once:

1. The typecheck, lint and unit tests for every part the pass touched.
2. **See every change run** where the owner will look at it, in one pass over the screens the notes name; fix what you see and recheck only that.
3. The slower tests that pin the changed surfaces, in one run. A failure in a file the pass did not touch is checked against HEAD's behaviour before it is called pre-existing.
4. `python tools/docs.py check` if any document changed.

## 5. Handoff and commit

The reply leads with the open choices (each look with what to compare), then one line per note (what changed), then "Defaults I chose", then what was verified and what was not. Commit (and push, if `CLAUDE.md` says so) before the reply, the body ending with one line for comparing passes:

`Feedback pass: <n> notes (<s> S / <m> M / <l> L); fix <k> dispatched, <calls> calls; lines changed <git diff --shortstat, excluding .md>`
