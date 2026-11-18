# package: build and verify in one session

For a package `SKILL.md` sized for this session, after its rules commit and baseline; chunks follow `.claude/agents/chunk.md` instead.

## Reading what you edit

- **Code you will edit:** whole when changed throughout, or short (under ~150 lines) and changed in more than two places; otherwise `sig`, its imports and the ranges you change (`sig Name:member` prints one member with line numbers), the opening's seams included.
- **A test file you add to:** its header, one test and the helpers it uses. **To add beside an anchor in a long file:** `git grep -n` the anchor and read a few lines there [AZ-145].
- **A sibling to copy:** Read it whole; `sig` the rest.

## Build

In logical commits, each `XX-nnn Name: <what it does>`.

- **Declare before use:** new types first, then the members others call, then their callers; imports in the same edit as their first use.
- Batch independent edits into one turn: each resends the conversation.
- **Changing a signature others call:** add the new form beside the old, move every caller in one turn, then remove the old.
- **Test expectations:** work each expected value out by hand first, watching for divisions and rounding that would pass a case trivially. A parser's fixture is taken from one real output of the tool it reads, never from memory [MM-139].
- When code makes a Built rule false, update the rule in the same change.
- **Check each novel seam the block plans is needed** against what already holds the data [AZ-141].
- **Unexpected scope:** what the outcome needs stays in; a useful extension becomes a peer package offered to the owner (with `forks: decide`, cut as a default); a discovery that breaks the boundary means stop and re-plan openly.

## Verify

With `python tools/verify.py` given `verify_steps` (`--resume` after a fix; read `working/verify/summary.md`, never a log), else the commands in `working-agreements.md` "Build and verify", quiet and filtered to pass and fail lines. Write tests for every behaviour a test can reach; a scheduled or timed thing exposes its step as a method returning what it did, so a test calls it directly. A package no test can reach writes none and says so. **Falsify the package's two or three key tests:** break the code each pins, watch it fail, undo the break with Edit; a test that stays green gets one more case, else say it is unproven. Two to five per package [PF-541]. The manual check's fixtures come before the first build (`handover.md`).

- **On a failure,** read `python tools/docs.py failures` before any rerun: the next run overwrites the report. A command ending `; echo exit $?` exits 0 itself.
- **A test whose result varies per run** (ordering, placement, neighbouring tests) passes a second run before it is committed [AZ-198].
- **Long real runs** start only once the code they run is final [MM-101]; a wait matches the command's own answer line, never a loose pattern [MM-110]; a measurement or load run that takes over the owner's machine waits for the owner's yes [MM-144].

Then `handover.md`. A package with nothing a test can't show still sets `built; awaiting the owner's check` and reports what to review.
