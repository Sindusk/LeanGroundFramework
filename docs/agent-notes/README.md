# Agent notes

How to work in this repository, by task. Design rules belong in `DESIGN.md`, not here. `CLAUDE.md` routes to these; open only the note the task needs, and only the section it names.

- `working-agreements.md`: Initiatives and Work Packages, design changes, open questions, writing documents, shell and editing, build and verify, debugging and investigations, manual checks, commits and handoffs, sessions and cost, skills and agents, the owner's preferences. Sections can be read on their own.
- `where-things-live.md`: where each system's code, data and docs are, how registration is wired, and the files to touch for each common addition. Open it before implementation work in a system you have not touched this session.
- `lessons.md`: lessons queued by package closes and routine sessions, waiting for a retro. Added with `python tools/docs.py lesson add`; read only in a retro.

Investigation notes are not agent notes: they live in `docs/investigations/`, indexed by its `README.md`.

Keep each fact in one note and link to it from others.
