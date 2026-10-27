# package: retro

Run only when the owner asks, in a session of its own, about every five closed packages. Package sessions change no skill, note or tool for a lesson: they queue it in `docs/agent-notes/lessons.md` (`close.md`).

1. **Measure.** If the owner has a cost script or dashboard, take the average cost per package since the last retro, the share by phase (opening, build, manual check, after the close), peak context and tool-result volume by kind, and compare with the figures under "Last retro" in `lessons.md`. Without one, work from the lessons alone and say so.
2. **Choose.** Act on a lesson that recurs, or that the measures show costing turns or context. A lesson seen once that cost little is dropped. Each change states, in its commit body, the cost it targets and the figure it should move.
3. **Change** the stage file, `where-things-live.md`, `tools/project_docs.py` or a hook. Rules, not stories: the step gets a bracketed package id and `why.md` the story. Prefer a mechanical check or a docs command over prose; trim before raising a budget (`python tools/docs.py budget`).
4. **Verify:** `python -m unittest tools/test_docs.py tools/test_hooks.py` if a tool changed, then `python tools/docs.py check`.
5. **Record:** remove the lessons acted on or dropped, and rewrite "Last retro" with today's date and the step 1 figures. Commit `Retro: <what changed>`, push if CLAUDE.md says so.
6. **Back to the kit:** a change to a core file (`tools/baseline.json` lists them) that would serve every project is offered to the owner for the Baseline kit too, as a one-line summary with the file and the change.
