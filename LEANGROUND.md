# Lean Ground Framework

A starting kit for a project built entirely through AI agents: a routing `CLAUDE.md`, a design document and a ledger, working agreements, a docs tool that reads one block at a time, and skills for designing and building Work Packages. It is extracted from Azothos (ProjectArcanum), PolarityFracture and CKReview.

**The kit is complete and has had one dry run.** Its phases:

1. **Scaffold:** layout, `AGENTS.md`, `CLAUDE.md`, `DESIGN.md`, `LEDGER.md`, history, questions, agent notes, `tools/leanground.json`. Done.
2. **Tooling:** `tools/docs.py` (with `tools/docs_sig.py`, the `sig` adapters for Java, Python and TypeScript/JavaScript, and a `tools/project_docs.py` plugin hook); the hooks in `.claude/settings.json` (`tools/search_gate.py`, `tools/edit_gate.py`, `tools/stop_check.py`); `.githooks/commit-msg` (`tools/commit_msg.py`) and `.githooks/pre-commit` (`tools/pre_commit.py`); tests in `tools/test_docs.py` and `tools/test_hooks.py`. Done.
3. **Skills and agents:** `.claude/skills/` `lg-package` (cut, build in one session, handover, close, retro, dispatch for oversized packages, `why.md`), `lg-design` (raise, round, record, consolidate, triage, working documents), `lg-feedback` (loose notes, sorted by size) and `lg-bootstrap` (interview, adopting existing code); `.claude/agents/` `chunk`, `fix` and `dig` (a read-only log reader). Budgets in `tools/leanground.json`, enforced by `docs.py check`. Done.
4. **Dry run:** a throwaway project bootstrapped and one package taken from cut to close; the cost measured and the kit fixed. Done (below).

## The dry run (2026-10-27)

Shelf, a Python command-line reading list, was taken from a fresh copy to its first closed package, each stage by a fresh agent reading the kit cold, with the owner's answers scripted. Calls and the context each stage ended at:

| Stage | Calls | Context |
|---|---|---|
| Bootstrap | 78 | ~127k |
| Design round, record, consolidate | 44 | ~113k |
| Cut (four packages; the rule attack raised three questions) | 23 | ~85k |
| Decisions on those questions, applied at once | 28 | ~97k |
| Build SH-100 (rules, code, 29 tests, five falsifications) | 62 | ~132k |
| Close | 20 | ~82k |

The package passed its five-step manual check first time. The run's findings were fixed in the kit: `docs.py` reads files before their first commit and decodes git's output as UTF-8 (a Windows crash in `close`), refuses outside a repository, takes rounds of questions already raised, removes answered rounds, refuses a draft with two question topics, flags a ledger block naming a closed question, and reads `tools/` for `sig`; the skills gained the clarifications the agents asked for. Compare later runs and retros with this table.

## Starting a project

Copy everything except `.git` into the new project's folder, then open a session there and say "bootstrap". From PowerShell:

```powershell
robocopy <framework folder> <new project folder> /E /XD .git
```

The lg-bootstrap skill runs `git init` if needed and `git config core.hooksPath .githooks`, interviews the owner, replaces the `{{…}}` placeholders, fills every `<!-- bootstrap: … -->` comment in the documents (then deletes the comment), writes `tools/leanground.json`'s project fields, seeds the ledger's Undesigned group, runs `python tools/docs.py check` and makes the first commit. `check` refuses a placeholder or bootstrap comment left behind once `leanground.json` says `"bootstrapped": true`.

## Core files and project files

**Core** files are the kit's: a project never edits them, and upgrading the project replaces them with the framework's newer copy. A project needing different behaviour adds a project file beside them (a `tools/project_docs.py` command, a project skill) rather than editing core. **Project** files start as skeletons and belong to the project once bootstrapped; an upgrade never touches them. `tools/leanground.json` lists the core files under `"core"`.

| File | Kind |
|---|---|
| `LEANGROUND.md`, `AGENTS.md` | core |
| `tools/docs.py`, `tools/docs_sig.py`, the hooks' scripts, their tests, `.gitattributes` | core |
| `.claude/skills/lg-{package,design,feedback,bootstrap}/`, `.claude/agents/{chunk,fix,dig}.md`, `.githooks/` | core |
| `CLAUDE.md`, `DESIGN.md`, `LEDGER.md`, `design-history.md`, `design-questions.md` | project |
| `docs/agent-notes/*`, `docs/archive/README.md`, `docs/investigations/README.md` | project |
| `tools/leanground.json` (its project fields), `tools/project_docs.py` | project |
| `.claude/settings.json`: its hooks are the kit's, its permissions the project's | both |

## Settings

`tools/leanground.json` holds what the tools and skills need to know about the project:

- `project`, `prefix`, `owner`, `collaborators`, `branch`: names the documents and tools use; `prefix` builds package ids (`AZ-104`).
- `bootstrapped`: false until the lg-bootstrap skill finishes; then `check` refuses any placeholder left.
- `push_on_commit`, `commit_trailer`, `commit_body`: the commit rules the Stop and commit-msg hooks enforce.
- `shell`: the primary shell, for the documents' command examples.
- `source_roots`: where the code lives, for `sig`, `close`'s record and `check`'s citations; empty means every tracked file.
- `long_file_lines`: past this, the search gate refuses a whole Read of a source file.
- `shell_read_paths`: globs, relative to the repository root (`docs/data/*.csv`), of small tracked data files the search gate lets the shell read beside a command; empty by default.
- `shell_window_lines`: the largest line window (`sed -n`, `head`, `tail`, `awk` on `NR`) of a tracked file the search gate lets the shell print; 60 by default.
- `section_cap`: tokens past which `docs.py` prints a design section with subsections as its own text and their menu, never whole; 5,000 by default.
- `handoff_past`: every session's context ceiling, which `docs.py context` reports against; past it, the session finishes the item in hand and gives the owner a paste-ready prompt for a new session. 200,000 by default.
- `retro_after_lessons`: past this many lessons queued in `docs/agent-notes/lessons.md`, `check` notes that a retro is due (a notice, never a failure); 15 by default.
- `test_report`: the JUnit-style XML report the test runner writes (a path, a folder or a glob), read by `docs.py failures`; empty until the project sets one.
- `commands`: `build` compiles or bundles, `test` runs the unit tests, `check_changed` runs the typecheck, tests and lint for only what the working tree touches, `verify` is the whole gate a package passes before its handover (build, tests, lint, `docs.py check`), `run` starts the app for a manual check, `stop` stops what a session started (dev servers, watchers). Each is empty until the project has one. `working-agreements.md` "Build and verify" gives each with its filter; agents read them there.
- `budgets`: tokens per file an agent loads unasked. `core`: the kit's files (see above).

## Hooks

- **Search gate** (`tools/search_gate.py`, before Bash, PowerShell and Read): refuses grep, cat, Get-Content and Select-String on tracked documents and source, and a whole Read of a source file longer than `long_file_lines`, naming the route to use instead. Logs, build output, untracked files, anything after a pipe and the data files `shell_read_paths` names pass. It also refuses:
  - a guessed line window over `shell_window_lines` of a tracked document or source (`sed -n 'A,Bp'`, `head -n N`, `tail -n N`, `awk 'NR>=A && NR<=B'`), naming the by-name readers: `python tools/docs.py sig <Name>`, a section or heading, Read with a range. A smaller window passes, as do the reads above that pass;
  - a search of the whole disk (`find /`, `find ~`, a recursive listing of a drive or the home folder), which on Windows outlives the tool's timeout and runs on unseen. Search a named folder instead.
- **Edit gate** (`tools/edit_gate.py`, before Bash and PowerShell): refuses `sed -i`, redirects, inline scripts and unreviewed scripts that rewrite a tracked file. `.claude/allow-shell-edits` opts a project out; `ALLOW_SHELL_EDITS=1` one command.
- **Stop reminder** (`tools/stop_check.py`): reminds the agent of uncommitted tracked changes, and of unpushed commits when `push_on_commit` is set.
- **Commit message** (`.githooks/commit-msg`, `tools/commit_msg.py`): the message ends with a `Co-Authored-By` trailer (`commit_trailer`), and has a body if `commit_body` is set.
- **Pre-commit** (`.githooks/pre-commit`, `tools/pre_commit.py`): a commit staging a budgeted file, anything under `.claude/`, `CLAUDE.md`, `AGENTS.md`, `LEDGER.md` or `DESIGN.md` runs `python tools/docs.py check` on the working tree and is refused with its output when it fails; any other commit is untouched. It works bootstrapped or not.

The gates answer Claude Code with exit 2 and Codex with its structured deny, so one copy serves both.

**Improvements flow back.** When a project's retro changes a core file, the change is made in the framework too, so the next project starts with it. Project-specific lessons stay in the project.

## Placeholders

- `{{PROJECT}}`: the project's display name.
- `{{PREFIX}}`: the Work Package ID prefix, two or three capitals (`AZ`, `PF`).
- `{{OWNER}}`: who makes the owner's decisions, as the documents name them.
- `{{BRANCH}}`: the branch commits go to.
- `<!-- bootstrap: … -->`: prose the bootstrap writes from the interview; the comment says what belongs there.
