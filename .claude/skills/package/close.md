# package: close a package or an Initiative

Both only on the owner's approval.

## Close a package

0. **If the owner approves but leaves part open** (a tuning, a design point the approval doesn't answer), raise it first as a 6.2 question written to stand alone with the values as built, cite it from the Built rules, check, and commit before the close. No package waits on it unless its answer needs code.
1. **`python tools/docs.py close XX-nnn [--steps N] [--delivered "the delivered <thing> (<section>)"]`** (N: the manual check's passing steps over every round; leave it out when there was none; `--date` if not today). It does the mechanical part and runs the check:
   - removes the package's ledger line and block and drops other lines' waits on it; with `--delivered`, rewrites bare mentions in other blocks to that text, and prints any mention needing rewording ("XX-nnn's panel") with its fields;
   - adds the history row;
   - appends the package's section to `docs/archive/initiatives/<date>-<initiative>-record.md` (created on the Initiative's first package; a standalone package gets its own), the block quoted unedited, the steps and, from git, the files and test files it changed with their new tests, and indexes it in `docs/archive/README.md`.
   Prose that names the package as history ("made in XX-nnn") stays as written.
2. **Fill the record's TODOs** with Edit (the prose only; Read from the package's heading): "Rules in `DESIGN.md` <sections and what each holds>"; *What was built*: the rules, then each code change by file, then the fixtures; *Verification*: the test lines are filled in, so edit them only to add a number that matters; the manual check "all N steps passed: <what was seen>", with numbers from the log. A new record's header also has a TODO for the Initiative's rule sections.
3. **Lessons:** at most three lines to `docs/agent-notes/lessons.md`, or none: `- XX-nnn: <what cost turns or went wrong, with a count> → <the change proposed>`. No skill, note or tool changes (`retro.md`).
4. Commit `Close XX-nnn Name: approved`, body "The package leaves the ledger and its block joins the <Initiative> record." Push if CLAUDE.md says so.
5. Stop: a recap only, with no question, button or card about the next package.

## Close an Initiative

After its last package closes (in the same session if the owner says so):

1. **`python tools/docs.py close-initiative "<Initiative>"`** (`--date` if not today). It refuses while any of its packages is on the ledger, then:
   - removes its ledger line, Contents entry and block; drops other lines' waits on it and names each;
   - writes the record's closing line, `## The Initiative as cut` quoting the block, and `### Left open at closing` with a TODO; marks the record closed in the index;
   - adds its `DESIGN.md` 6.4 Delivered paragraph with TODOs, and the history row naming the lines freed;
   - names a working document to move, and lists every remaining mention of it or its packages in the live documents and `tools/*.py` as `file:line`.
2. **Fill the TODOs** with Edit: the 6.4 paragraph's user-facing prose (what a user now has, in one sentence of clauses), its rule sections, what stays open or moved; the record's "Left open at closing" bullets. Then the listed mentions: a block naming one of its packages as a dependency reads "the delivered <thing> (<section>)"; history stays.
3. A working document moves unedited (`git mv`) beside the record, same date prefix.
4. `python tools/docs.py check`.
5. Commit `Close the <Initiative> Initiative`, body: the packages, what was left open, the lines freed. Push if CLAUDE.md says so.
