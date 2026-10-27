# package: fixtures, checklist, launch

The manual check covers only what a test can't: look, layout, feel, sound, a real device or service, plus a short smoke run of the main path. Steps a test proved are left off. How the owner runs the app and sets up state is in `working-agreements.md` "Manual checks".

## Fixtures

Set up the state the checklist reads with a fixture the project already has (a seed, a script, a debug command, a test account), extended for this package; never steps the owner performs by hand to reach the starting state. A fixture holds exactly what the current checklist uses, and is safe to run again on a long-lived environment.

- **Debug controls never need ids or coordinates the tester must look up:** they act on what is selected, open or nearest.
- Stations the checklist builds on and the tester keeps (accounts, sample data that later checks reuse) go in a setup step the fixture can run without clearing anything.

Then walk the checklist in these passes, before writing it:

1. **Holds.** Could what the tester must read change before they read it (a timer, a poll, a background job, a cache expiring)? Then add a hold or step control first and put every hold in the checklist's first steps. Never make the tester race a timer.
2. **Numbers.** Draft each step's expected read-out before the fixture's values, then choose values whose results are unambiguous: no ties, rounding or caps hiding the rule. Give the expected value in the step, worked from the rules, never recalled [AZ-177].
3. **State.** List what each step assumes (accounts, flags, permissions, prior data) and make the fixture set each, revoking what must not be there: the tester's environment is long-lived, never fresh. A fixture's markers (names, colours, ids) are ones no other fixture uses [AZ-161].
4. **Environment.** Screen size, browser, locale, time, network: put each assumption in the fixture or the step. Check every size a layout claims against the real window [AZ-177].
5. **Reachability.** Each step's condition must be reachable in real use, not only in a test [AZ-183].
6. **Tuning.** A value the owner will judge by eye or feel gets a live control, so it is tuned without a relaunch. Record the tuned value in the rules.
7. **Promises.** Check each step's claim against the Built rules, not memory.

## Hand over

`python tools/docs.py status XX-nnn "built; awaiting the owner's check"`, then one commit with the fixtures: `XX-nnn Name: the fixtures; built`. Report what was done, what isn't, the tests that replaced checklist steps, and "Defaults I chose". For a screen or art, list **your readings** of the block's visual words, one line each, before the checklist, so the owner can redirect before the first launch. Then the checklist, holds and environment first, as short as the unchecked behaviour allows (rounds cost, not steps):

- It starts with the fixture's command.
- One action per step, then what the tester should see. Repeats of one action are one step. No arrows, no chained actions.
- Don't spell out keys; be explicit where it changes the result. Warn before a step that hides information.

The tester reports in short rounds; answer with the failing step's follow-ups or the next round's step numbers, never the whole list again. Rounds are a session's most expensive turns.

## Launch

**Only on the owner's go-ahead**, after the report and checklist, and a relaunch too. Reuse a server the owner keeps running rather than starting a second. Run the app in the background and watch its log with a Monitor whose filter passes only warnings and errors from the project and ends itself when the app stops, since every event is a whole turn. Stop a running watch (TaskStop) before a relaunch. Take exact read-outs from the log where it records them rather than asking the tester.

A failing step gets focused follow-up steps and a fix commit; the package stays open until the owner approves.
