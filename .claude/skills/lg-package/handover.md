# package: fixtures, checklist, launch

The manual check covers only what a test can't: look, layout, feel, sound, a real device or service, plus a short smoke run of the main path. Steps a test proved are left off. How the owner runs the app and sets up state is in `working-agreements.md` "Manual checks".

## Fixtures

Set up the state the checklist reads with a fixture the project already has (a seed, a script, a debug command, a test account), extended for this package; never steps the owner performs by hand. A state one command sets (an empty scratch path) needs no fixture: that command is the checklist's first step. A fixture holds exactly what the current checklist uses, is safe to run again on a long-lived environment, and passes its values by name [AZ-173].

- **Debug controls never need ids or coordinates the tester must look up:** they act on what is selected, open or nearest.
- **What the checklist consumes is in the always-run part;** a run-once setup step, which clears nothing, holds only what is reused as it stands (accounts, sample data later checks keep) [AZ-173].

Then walk the checklist in these passes, before writing it:

1. **Holds.** Could what the tester must read change before they read it (a timer, a poll, a background job, a cache expiring)? Then add a hold or step control, every hold in the checklist's first steps; never make the tester race a timer.
2. **Numbers.** Draft each step's expected read-out before the fixture's values, then choose values whose results are unambiguous: no ties, rounding or caps hiding the rule. Give the expected value in the step, worked from the rules, never recalled [AZ-177].
3. **State.** List what each step assumes (accounts, flags, permissions, prior data) and make the fixture set each, revoking what must not be there: the tester's environment is long-lived, never fresh. Every object a step uses comes from the fixture, matched by exact kind and variant, not name [AZ-160]; one the tester creates mid-checklist lacks the fixture's preconditions [AZ-196]. A fixture's markers (names, colours, ids) are ones no other fixture uses [AZ-161].
4. **Environment.** Screen size, browser, locale, time, network: put each assumption in the fixture or the step. Check every size a layout claims against the real window [AZ-177].
5. **Reachability.** Each step's condition must be reachable in real use, not only in a test [AZ-183].
6. **Tuning.** A value the owner will judge by eye or feel gets a live control, so it is tuned without a relaunch. Record the tuned value in the rules.
7. **Promises.** Check each step's claim against the Built rules, not memory.
8. **Dry run.** Run every command the checklist names once against the built app, and trace each state that locks or accumulates through the steps in order [AZ-198].

## Hand over

`python tools/docs.py status XX-nnn "built; awaiting the owner's check"`, then one commit with the fixtures, if any: `XX-nnn Name: the fixtures; built` (else `XX-nnn Name: built`). Where the package print says `close: on_build` and no manual check is left, go straight on to `close.md`. Report what was done, what isn't, the tests that replaced checklist steps, and "Defaults I chose" from the note (first, with `forks: decide`). **A changed screen** is rendered and looked at by you first; a defect you can name in your own render is fixed, not listed [PF-529]. Candidates that differ in arrangement are settled with mock-ups in chat before building [MM-127]. For a screen or art, list **your readings** of the block's visual words, one line each, before the checklist, so the owner can redirect before the first launch. Then the checklist, holds and environment first, as short as the unchecked behaviour allows (rounds cost, not steps):

- It starts with the fixture's command. You run every command and put its output in chat; the owner only uses the app [MM-102].
- One action per step, then what the tester should see. Repeats of one action are one step. No arrows, no chained actions. A multi-part setup is one step per part, each naming the fixed point it is relative to [AZ-167].
- Don't spell out keys; be explicit where it changes the result. Warn before a step that hides information.

Answer each round with the failing step's follow-ups or the next round's step numbers, never the whole list again: rounds are a session's most expensive turns.

## Launch

**Only on the owner's go-ahead**, after the report and checklist, and a relaunch too. Reuse a server the owner keeps running rather than starting a second. Launch the app in the background, say so in one line, and end the turn: no Monitor, tail or poll of its log, since every event is a whole turn [AZ-191, MM-145]. A background process's completion notice gets no reply [AZ-209]. **On the owner's report**, read the log once (a long one through a `dig` subagent), errors and logged read-outs in one call with known noise filtered, and take exact read-outs from it rather than asking the tester; where a step's exact text is the evidence on a transient, unlogged surface, make it logged output or accept the tester's report and say so at close. Read it before any relaunch too, since a launch overwrites it; stop the running app (TaskStop) first.

A failing step gets focused follow-up steps and a fix commit; the package stays open until the owner approves.
