# package: build and verify in one session

For a package `SKILL.md` sized for this session, after its rules commit. A dispatched build never reads this file: its chunks follow `.claude/agents/chunk.md`.

## Reading what you edit

- **Code you will edit:** whole when short (under ~150 lines) or changed throughout; otherwise `sig`, then its imports and the ranges you change (`sig Name:member` prints one member with line numbers). The seams located at the opening are read this way, since you edit them.
- **A sibling to copy:** Read it whole; `sig` the rest.

## Build

In logical commits, each `XX-nnn Name: <what it does>`.

- **Declare before use:** new types first, then the members others call, then their callers; imports in the same edit as their first use.
- Batch independent edits into one turn: every turn resends the conversation.
- **Changing a signature others call:** add the new form beside the old, move every caller in one turn, then remove the old.
- **Test expectations:** work each expected value out by hand first, checking for exact divisions and rounding that would make a case pass trivially.
- When code makes a Built rule false, update the rule in the same change.
- **Check each novel seam the block plans is needed** against what already holds the data [AZ-141].
- **Unexpected scope:** what the outcome needs stays in; a useful extension becomes a peer package offered to the owner; a discovery that breaks the boundary means stop and re-plan openly.

## Verify

With the commands in `working-agreements.md` "Build and verify", run quietly and filtered to their pass and fail lines. Write tests for every behaviour a test can reach; a scheduled or timed thing exposes its step as a method returning what it did, so a test calls it directly. **Falsify the package's two or three key tests:** break the code each pins, watch it fail, undo the break with Edit; a test that stays green gets one more case, else say it is unproven. Two to five per package [PF-541]. Write the manual check's fixtures before the first build (`handover.md`), so one build covers everything.

Then `handover.md`. A package with nothing a test can't show still sets `built; awaiting the owner's check` and reports what to review.
