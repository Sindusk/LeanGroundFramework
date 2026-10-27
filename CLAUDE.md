# {{PROJECT}} — Workspace Instructions

<!-- bootstrap: one paragraph: what the project is, its stack and versions, its identifiers (package name, app id), the repository (owner/name, branch {{BRANCH}}), the OS and the primary shell. -->

## What to read for a task

Read the lines that apply, then stop. Notes are in `docs/agent-notes/`; read the named section, not the whole file.

**Read one block at a time with `python tools/docs.py`:** a design section (`4.2`), a package (`{{PREFIX}}-nnn`), an Initiative (`"<name>"`), a question (`q12`), a system's code (`where <system>`); `python tools/docs.py help [command]` for the rest. Don't open or print `DESIGN.md` or `LEDGER.md` whole, by any tool (`python tools/docs.py ledger` gives the ledger's lines). Brief a subagent with the `docs.py` commands it needs, not files to read, and give a long session's next stage a new session. A section or package a block cites is a lookup for when the work needs it, not an instruction to read it.

- **A new project** (`tools/leanground.json` says `"bootstrapped": false`): the bootstrap skill, before anything else.
- **Anything:** the `DESIGN.md` section for the system you touch. Section 4's **Built rules** subsections are what the code does; 2 is the constraints, 6 the roadmap, 7 performance.
- **Cutting, building or closing a Work Package or Initiative:** the package skill, which holds the procedure; it starts a build with `python tools/docs.py {{PREFIX}}-nnn`. **The ledger's format and who decides:** `working-agreements.md`, "Initiatives and Work Packages". After editing `LEDGER.md`, run `python tools/docs.py check`.
- **Changing the design, open questions, rounds, loose ends:** the design skill.
- **A batch of the owner's notes or polish requests:** the feedback skill.
- **Implementation:** `python tools/docs.py where <system>` for where a system's code, tests and data are, `where "recipe: <kind>"` for the files a new kind of thing touches; `working-agreements.md` "Build and verify". Code you only call: `python tools/docs.py sig <name>`, never a Read; a file you will edit: whole when short, else its imports and the ranges you change.
- **Committing or handing off:** `working-agreements.md` "Commits and handoffs".
- **How the owner likes to work:** `working-agreements.md` "Owner preferences".
- **Something delivered:** `docs/archive/` (its `README.md` indexes it). Never authoritative.

## Always

- **Design first:** behaviour goes into `DESIGN.md` and gets the owner's review before coding; a behaviour change gets a dated row in `design-history.md`.
- **Roadmap discipline:** an Initiative is something a user or the owner would notice; its buildable parts are Work Packages with permanent `{{PREFIX}}-` ids from the ledger, `LEDGER.md`. Docs, tooling and fixes are just work, with no id. Moving items on the ledger and approving work are the owner's decisions.
- **Record questions, don't ask them:** a design choice found during any work becomes a numbered question in `DESIGN.md` 6.2; a loose end left unfixed goes in 6.7.
- **Debugging:** after two failed fixes for one symptom, stop guessing and add labelled diagnostics. Measure; never adopt a placeholder number.
- **Editing:** Edit for existing files, Write for new ones; never write files through the shell. Match the surrounding code's style and comment density.
- **Commits:** commit at logical checkpoints and push each commit to `{{BRANCH}}` once it is made: leave to commit is leave to push. A package's commit subject leads with its id and name. End with a blank line and the trailer naming the model that made the commit: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
<!-- bootstrap: drop the push clause above if the owner pushes by hand. Then add the project's own always-rules, one bullet each, citing their DESIGN.md section: its layering rule (section 3), performance rules (7), safety rules ("never deploy", "never create a database without approval"), public-repository rules (2). Keep this file within its budget: `python tools/docs.py budget`. -->
