---
name: design
description: Run design work — raise open questions in DESIGN.md 6.2, write question rounds, assess where ledger items stand, record the owner's answers, consolidate decisions into the design and its history, open an Initiative's working document. Use when the task changes what the product should do (a rule, a system, a behaviour), when the owner says "round", "record the answers" or "consolidate" or asks a design question, and before code that needs a rule DESIGN.md doesn't state.
argument-hint: "[raise | round | record | consolidate | triage]"
---

# design

How a design question moves from gap to rule. Standing rules: `working-agreements.md` "Design changes" and "Open questions and loose ends", and `DESIGN.md` 6.2's opening.

Read blocks with `python tools/docs.py`, never whole files: `6.2 --own` for the question rules and the next free number, `q14` for one question (in 6.2 or a working document), the touched section (`4.3`) for context, `round` for the current round.

**Let the tool do the mechanical writes.** `python tools/docs.py raise <draft>` and `round add <draft>` number drafted questions and write them, with a round and its glossary terms (`rounds-and-triage.md` gives the draft's shape); `record` moves a round's answers into decisions; `drop q14 q9` and `drop DESIGN.md "<heading>"` remove questions and blocks; each then runs the check. An Edit that deletes text quotes it whole; the tool costs a line.

**One stage per session where the work allows:** every turn resends the whole conversation. Finish a stage, commit, and suggest a new session for the next.

## The stages

Each stage is its own commit with an ordinary subject (no package id unless a package is being built). Never skip ahead: a recorded decision is not a rule until consolidated, and consolidation happens only when the owner asks.

| Owner says / situation | Stage |
|---|---|
| A gap found while cutting, building or reviewing | 1. Raise |
| "Write a round", several open questions want answers together | 2. Round |
| Several rounds at once, drafted by subagents | `rounds-and-triage.md` |
| "Where should these items move?" | `rounds-and-triage.md`, Triage |
| Answers are filled in `design-questions.md`, or given in chat | 3. Record |
| "Consolidate" | 4. Consolidate (`consolidate.md`) |
| An Initiative's design outgrows a few questions | `working-documents-and-backlog.md` |
| A backlog pitch is promoted, parked or retired | `working-documents-and-backlog.md` |

## 1. Raise a question

- Draft it as `## Questions: DESIGN.md <topic>` with `- **G1.** …` items and run `python tools/docs.py raise <draft>`: it takes the next free number in 6.2, files it under its `#####` topic and bumps the number. Numbers are permanent: never reuse or renumber.
- Content, in one bullet: the gap and where the design is silent (cite sections), the candidates as **(a)**, **(b)** where there are any, where it was found ("Found cutting <Initiative>", "Found in XX-nnn"), then **Recommendation:** with its tradeoff and **Cost of being wrong:**.
- **Keep the bullet short when a round will carry it:** the plain-language explanation is the round's.
- Only real choices go to the owner. Routine details are decided in the document and said so.
- If the question holds a package, the package's ledger line says "waits on question N".
- A question belonging to an Initiative with a working document is asked there instead, and 6.2 gets a short note under a heading naming the document and the numbers.
- Tuning numbers go to `DESIGN.md` section 11, not 6.2. A loose end that is not a design choice (docs disagree with code, a TODO) goes to 6.7.
- Don't ask a raised question in chat on its own: point at its number; questions reach the owner through a round.
- **Left for a collaborator** (one named in `tools/baseline.json`, answering with their own agent): leave the questions open and record no decision; add a note in 6.2 naming them and the packages they hold, and append "; questions N to M open, left for <name>" to the Initiative's ledger line. Write each to stand alone for an agent reading it cold.

## 2. Write a round

A round batches open questions into `design-questions.md` for a reader **outside the project** (the owner may answer with someone else).

- A new round goes after the rounds still open. `record` removes a round once nothing in it is left to answer, and names it on the "Answered rounds" line.
- Heading: `## Round N (YYYY-MM-DD): <what it settles>`, then a short paragraph saying what the round frees (which packages each question holds, which are built to the recommendation and need only a yes), in the order that frees the most work.
- Group questions under `###` topic headings with a plain-language framing paragraph. Each question:

```
#### Q<number>. <the question in plain words>

**Explanation:** what the design already says, in terms the glossary covers.

**Gap:** what is open. Holds XX-nnn <name>.   (or "Holds no package")

**Options:**

* **(a) Short name:** ...
* **(b) ...**

**Recommendation:** (a). Why, and the tradeoff against the others. Cost of being wrong: …

> **Response:**
```

- Keep the glossary at the top current: add a term the round relies on, rename terms the design renamed.
- Question numbers are DESIGN.md's; a round restates them, it doesn't mint new ones. Write the round as a draft and add it with `python tools/docs.py round add <draft>`: questions already raised are headed by their numbers (`#### Q12.`), new ones by placeholders with their `## Questions:` part.
- Commit: `Design questions round N: <topic>`, body listing the questions.

**Then put the round to the owner in chat; this is the default.** Print it with `python tools/docs.py round` and ask its questions directly, in its order: per question its number and plain question, its explanation (condensed from Explanation and Gap to read without the file), what it holds, the options by letter in a few words each, and the recommendation with its reason in a sentence. Ask for answers by number ("14 rec, 15 a, 16 b but …"). **Rounds are asked in order, one at a time.** **Before asking a round, bring it up to date** where an earlier answer changes a later question's framing or recommendation, so the file, the chat and the recorded decision agree.

## 3. Record answers

1. **`python tools/docs.py record 14=rec "15=(b), because …" "16=not yet: …"`** (`--by <who>` if not the owner, `--date` if not today), each answer verbatim; with none it reads the Responses filled in the file. It writes each answered question's decision under it, complete for a plain "rec", else a stub with a TODO; removes the question from the round; leaves "not yet", "discuss" and blank responses.
2. **Replace each stub's TODO** with what departs from or adds to the recommendation, and why; what is unverified. Don't restate the recommendation. `check` reports any stub left.
3. A partial answer: record the decided part, and keep or raise follow-ups.
4. Commit: `Record round N's answers: questions …`, naming in the body any decision that overrules the recommendation.

When the owner decides in chat and asks for the result applied at once ("go ahead as you suggest"), recording and consolidating are one commit: stage 4's steps, with the decision in the history row's Reason. Run `record` only for questions in a round; a question never put in one goes straight to consolidation.

## 4. Consolidate (only when the owner asks)

Read `consolidate.md` beside this file and follow it.

## Throughout

- **Measure before recommending housekeeping.** Size a file, count rows or read the section first; a suggestion dropped after measuring costs the owner a decision for nothing.
- Writing format (blank lines before lists, bold numbers for cited lists) is in working-agreements' "Writing documents".
