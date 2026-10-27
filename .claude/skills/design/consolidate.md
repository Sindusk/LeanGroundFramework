# design: consolidate

Only when the owner asks. **Consolidate after each recorded round** rather than letting rounds pile up: many rounds in one pass costs every late turn the whole history. Consolidating and cutting new packages are separate sessions unless the owner asks for both.

## Steps

For each decided question, usually several at once (`python tools/docs.py decisions --all` lists them):

1. **The rule into `DESIGN.md`**, in the system's design section, present tense, no "used to" or "no longer". **Built rules subsections state what the code does**, so a rule that changes built code goes into the design section with one sentence saying the built code differs until its package lands. Keep section 7 true if the rule has a cost, and section 11 if it leaves tuning.
2. **The reason into `design-history.md`**: one dated row per decision or closely related group, the Decision cell stating the rule with the section it lives in, the Reason cell why, naming who decided and why a recommendation was overruled; "question 14", not "Q14". Write the rows to a file and append them with `python tools/docs.py history add <file>`, which validates them. **A removal is a decision too:** a deleted rule or pitch gets its row.
3. **Remove the questions** with `python tools/docs.py drop q14 q9 …`, and each 6.2 note it reports left empty with `drop DESIGN.md "<note>"`. From a working document, also follow `working-documents-and-backlog.md`; pitches leaving the backlog likewise.
4. **The ledger:** lines that waited on these questions say what they now wait on, or "can be built"; blocks whose *Scope* or *Done when* named a question cite the section instead. Moving an item between groups is the owner's call.
5. **Every consolidated rule gets a home; nothing is orphaned:** the package that builds it, else its Initiative's block, else a new package cut there (the package skill's `cut.md`, inserted with `python tools/docs.py ledger insert <file> --after XX-n`). Where no Initiative fits, raise a question asking where it lives, with a recommendation.
6. **Sweep for orphans:** `python tools/docs.py orphans`, and 6.7's lines saying the design is ahead of the code. Each hit is homed as in step 5, or is an open matter already asked.
7. A heading added, renamed or removed: replace `## Contents` with `python tools/docs.py toc DESIGN.md`. Grep for citations of dropped questions and pitches.
8. `python tools/docs.py check`; fix what it reports.
9. Show the owner the change before committing (a change they asked for in so many words counts as reviewed once they've seen it), then commit: `Consolidate <rounds or questions>: <what moved where>`, body grouping the rules by section and naming the packages freed and cut.

## Splitting a large pass

More than a dozen questions, or rules landing in many sections: split by **section ownership**, one agent per group of disjoint `DESIGN.md` sections, each in its own worktree (`isolation: "worktree"`), so git merges their edits. Drafting suits Sonnet; the lead reviews and decides homes.

- **The brief comes from `python tools/docs.py decisions q14 …`**, not from reading 6.2 whole.
- **Agents edit only their sections.** 6.2, the backlog, section 11, the Contents, `LEDGER.md` and `design-history.md` are the lead's; agents report what those need.
- **Agents return files, not prose:** history rows in a scratch file for `history add`, package blocks for `ledger insert`. The lead appends them with the tools rather than retyping them.
- The lead merges, reviews only the added lines, squashes the drafts into one uncommitted change for the owner's review, and removes the worktrees.
