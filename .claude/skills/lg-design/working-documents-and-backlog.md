# design: working documents, the idea backlog and loose ends

## A working document for an Initiative

One file under `docs/initiatives/`, named for the Initiative, headed "working document, not authority", with a "Where it stands" paragraph and a `## Open questions` heading, where its questions are raised (`raise` with `## Questions: docs/initiatives/<x>.md`). Add the path as an indented line under the Initiative's ledger line, then `python tools/docs.py check`. Decisions still consolidate into `DESIGN.md` and `design-history.md`.

**Consolidating from it:** also cut what `DESIGN.md` now states to a pointer at the sections, and update its "Where it stands" (consolidated, still open, cut or not) and the 6.2 note naming its questions.

When the Initiative closes, the document moves unedited to `docs/archive/initiatives/` beside its record (the lg-package skill's `close.md`).

## The idea backlog

`DESIGN.md` 6.2's **Idea backlog** holds lettered pitches, each a `##### A. Name` heading: proposals, never rules. A pitch is promoted (its mechanic designed into a section), parked, or retired by a question like any other. When one leaves:

- `python tools/docs.py drop DESIGN.md "<letter>. <name>"` removes its entry; add its letter to a "Retired letters" line in the backlog's opening paragraph. Letters are never reused.
- Grep for "pitch <letter>" and remove or replace each citation (a rule cites the section it now lives in).
- Ideas worth keeping move to where they will be used (an Initiative's block, a working document), not lost with the entry.
- A history row, as for any removal.

## Loose ends

- **Before working a 6.7 entry, check it still applies;** close or reword a stale one before fixing anything.
- **A sweep starts with a map** sorting 6.7's entries by what each needs (a fix here, a run, the owner's eye, a design question); the owner picks the groups, one commit a group.
