# design: batch rounds and ledger triage

## Triage: where an item stands

When the owner asks where ledger items should move, read the lines (`python tools/docs.py ledger`), each item's block and the sections it cites, and the open questions it names; then recommend, and move nothing until the owner says (working-agreements, "Who decides what").

- **Undesigned → Designed:** `DESIGN.md` states its shape (what it is, what it builds on, its rules in outline) and only named choices remain. Its line then says, after the dash, exactly what stands before Work-Ready.
- **Designed → Work-Ready:** nothing but tuning (section 11) and choices a builder records stands in the way of a cut. A question that would hold one package can stay open: the cut writes it on that package's line.
- Stays Undesigned while its core mechanic is open or its rules live only in starting notes.

## The draft's shape

`python tools/docs.py raise <draft>` and `round add <draft>` read a scratch file in this shape:

- `## Questions: DESIGN.md <topic>` (a `#####` topic of 6.2's Open questions, made if new) or `## Questions: docs/initiatives/<x>.md`: an optional note paragraph, then one `- **G1.**` item per question, ids being placeholders (letters and a number), cross-references written `G2`, `QG2` or `questions G1 and G2`.
- `## Round N (date): <what it settles>`, in the round format of `SKILL.md` stage 2, its questions headed `#### QG1.`; they are numbered in the round's order. Only for `round add`.
- `## Glossary`: `- **Term:** definition` lines; terms already in the glossary are skipped and named, to amend by hand.

Each writes nothing unless every part fits, then checks. By hand afterwards: the ledger lines naming the questions, and for a working document a note under a 6.2 heading naming it and the numbers.

## Batch rounds: several drafted at once

1. **Brief one drafter per round** (an Initiative or two that overlap), `model: "sonnet"`: the `docs.py` commands and sections to read, never whole files; draft only, into one scratchpad file, nothing tracked edited. Drafting may run in parallel.
2. **Integrate in order, one round a commit:** review each draft against the others (an answer one round's question depends on, shared data, a term two drafts name differently), fix it in the scratchpad, then `round add`.
