# Baseline

A starting kit for a project built entirely through AI agents: a routing `CLAUDE.md`, a design document and a ledger, working agreements, a docs tool that reads one block at a time, and skills for designing and building Work Packages. It is extracted from Azothos (ProjectArcanum), PolarityFracture and CKReview.

**The kit is not ready to use yet.** Phase 1 (this layout and the document skeletons) is done; the tooling and skills the documents name do not exist yet:

1. **Scaffold:** layout, `AGENTS.md`, `CLAUDE.md`, `DESIGN.md`, `LEDGER.md`, history, questions, agent notes, `tools/baseline.json`. Done.
2. **Tooling:** `tools/docs.py` (generic core, `sig` adapters per language, a `tools/project_docs.py` plugin hook) with `tools/test_docs.py`; `tools/search_gate.py`; `.claude/settings.json` with the search gate, a shell-edit gate and a Stop hook reminding of uncommitted or unpushed work; `.githooks/commit-msg` checking the trailer.
3. **Skills and agents:** `.claude/skills/` `package` (cut, build, handover, close, retro, dispatch for oversized packages, `why.md`), `design` (raise, round, record, consolidate), `feedback` (loose notes, sorted by size) and `bootstrap`; `.claude/agents/` `chunk` and `fix`. Budgets enforced by `docs.py check`.
4. **Dry run:** a throwaway project bootstrapped and one package taken from cut to close; the cost measured and the kit fixed.

## Starting a project

Copy everything except `.git` into the new project's folder, then open a session there and say "bootstrap". From PowerShell:

```powershell
robocopy C:\Users\sinis\Documents\Baseline <new project folder> /E /XD .git
```

The bootstrap skill interviews the owner, replaces the `{{…}}` placeholders, fills every `<!-- bootstrap: … -->` comment in the documents (then deletes the comment), writes `tools/baseline.json`'s project fields, seeds the ledger's Undesigned group, runs `python tools/docs.py check` and makes the first commit. `check` refuses a placeholder or bootstrap comment left behind once `baseline.json` says `"bootstrapped": true`.

## Core files and project files

**Core** files are the kit's: a project never edits them, and upgrading the project replaces them with Baseline's newer copy. A project needing different behaviour adds a project file beside them (a `tools/project_docs.py` command, a project skill) rather than editing core. **Project** files start as skeletons and belong to the project once bootstrapped; an upgrade never touches them. `tools/baseline.json` lists the core files under `"core"`.

| File | Kind |
|---|---|
| `BASELINE.md`, `AGENTS.md` | core |
| `tools/docs.py`, `tools/test_docs.py`, `tools/search_gate.py` | core |
| `.claude/skills/{package,design,feedback,bootstrap}/`, `.claude/agents/{chunk,fix}.md`, `.githooks/` | core |
| `CLAUDE.md`, `DESIGN.md`, `LEDGER.md`, `design-history.md`, `design-questions.md` | project |
| `docs/agent-notes/*`, `docs/archive/README.md` | project |
| `tools/baseline.json` (its project fields), `tools/project_docs.py`, `.claude/settings.json` | project |

**Improvements flow back.** When a project's retro changes a core file, the change is made in Baseline too, so the next project starts with it. Project-specific lessons stay in the project.

## Placeholders

- `{{PROJECT}}`: the project's display name.
- `{{PREFIX}}`: the Work Package ID prefix, two or three capitals (`AZ`, `PF`).
- `{{OWNER}}`: who makes the owner's decisions, as the documents name them.
- `{{BRANCH}}`: the branch commits go to.
- `<!-- bootstrap: … -->`: prose the bootstrap writes from the interview; the comment says what belongs there.
