# package: close a package or an Initiative

Both only on the owner's approval. Where the package print ends `close: on_build`, "build XX-nnn" was it for a package: build, verify, commit, close, report, stop, steering coming later as feedback passes; only a named reviewer, a failure you cannot fix or a manual check the owner did not waive holds it open [PF cost analysis 2026-10-26].

## Close a package

0. **If the owner approves but leaves part open** (a tuning, a design point the approval doesn't answer), raise it first as a 6.2 question written to stand alone with the values as built, cite it from the Built rules, check, and commit before the close. No package waits on it unless its answer needs code.
1. **`python tools/docs.py close XX-nnn [--steps N] [--delivered "the delivered <thing> (<section>)"]`** (N: the passing steps of every round, a fix's recheck steps included; a step wrong by the checklist, not the package, is left out and the record names it; no `--steps` when there was no check; `--date` if not today). It removes the line and block and the waits on it (with `--delivered`, rewrites bare mentions, printing any to reword), adds the history row and the archive index entry, and appends the package's section to its Initiative's record (`help close`): the block unedited, the steps, the build commit and from git the files and tests changed; from the note its rulings, defaults, not done and dispatch line, its lessons queued [MM-101]. Place by hand any line it prints as unplaced. Prose naming the package as history stays.
2. **Fill the record's TODOs** with Edit (Read from the package's heading), one line each, since the build commit's body is the full account: the rule sections and what each holds; *What was built*, the rules, then each code change by file, then the fixtures; the manual check's "<what was seen>", numbers from the log. A new record's header also has a TODO for the Initiative's rule sections. Each not-done item also goes into the block of the package that owns it, or 6.7.
3. No skill, note or tool changes for a lesson (`retro.md`); remove `working/pending/XX-nnn/` after the commit.
4. **Stop what the session started:** read the log if the last report didn't (`handover.md`, Launch), then run `commands.stop` (or stop what you launched) unless a test run is live or the owner is in the app [PF retro 2026-11-15].
5. Commit `Close XX-nnn Name: approved`, body "The package leaves the ledger and its block joins the <Initiative> record." Push if CLAUDE.md says so.
6. Stop: a recap only, with no question, button or card about the next package.

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
