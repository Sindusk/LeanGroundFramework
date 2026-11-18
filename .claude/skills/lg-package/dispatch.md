# package: dispatch a build to chunk subagents

For a build too large for one context (`SKILL.md` step 2). The session becomes the **manager**: it plans, briefs, checks, commits and closes on a small context, and each chunk runs in a fresh `chunk` subagent (`.claude/agents/chunk.md`) whose context ends with the chunk. Briefs and reports travel as files under `working/pending/XX-nnn/` (gitignored; remove the folder after the close). The manager edits inline only a few lines.

## 1. The Build plan

Write plan.md in that folder: the package id, the rule sections, the seams already found as `file:line` rows, then one to four chunks, in dependency order (a shared rule before its readers):

```markdown
1. <chunk>: <deliverable>; files <list>; consumes <exact names and types from earlier chunks, or none>; produces <exact exports, routes, fields later chunks use>; copies <a sibling file or an earlier commit, git show --stat <sha>>; done when the tests (a) <named case and what it asserts>, (b) …; falsify (a); verify <the commands>  (S s, K k, T t)
```

- **"Done when" is a numbered list of named tests**, one per criterion and per clause of the rule the chunk builds. The report ticks each by letter [PF-537].
- **Consumes and produces match across lines exactly**: signatures and values, never bodies; a value the design lets stack is produced as a list [PF-533].
- **The plan spends the package's two to five falsifications** as "falsify (x)" clauses on its foundation tests; a chunk with none falsifies nothing [PF-541].
- **An exception in a rule names its effects**, never "any" or "every": a chunk builds the text literally [PF-536].
- **Tally each line as (S, K, T):** S new site lists (a kind of addition `where-things-live.md` gives a recipe for, a new message or event with its readers), K the codebase's largest, most-read files it edits, T its tests. **Split where S ≥ 2, or T > 5 with K ≥ 1** [PF-535]. Under about 20 files is one chunk: each extra chunk costs a cold start and a check [PF-539]. Size each to end near 100k of context, never past about 250k.
- A chunk adding a member to a shared type owns every exhaustive reader of it, listed in its files [PF-536].
- A chunk the owner must judge by eye stays with the manager: the subagent builds it, the manager shows it and asks.

## 2. One chunk at a time

Never two at once: they share the tree, the servers and the test runners. Write `chunk-<n>-brief.md`: the package and rule sections (as `docs.py` commands), the chunk's plan line, the decisions taken so far, "Read first" (where each wiring joins: the function and the line [PF-536]; declarations as `sig` commands, a file only where the chunk edits most of it [PF-541]), every earlier report's "Produced" part whole and its "Not done" as deviations, and "Not yours" (other chunks' files and anything already modified). The brief is the chunk's single source of requirements.

Dispatch in the foreground with Agent, `subagent_type: "chunk"`; `model: "sonnet"` only for a chunk that copies a sibling with no K file. The prompt is only:

```
Build chunk <n> of package XX-nnn in <repo path>. Your brief is working/pending/XX-nnn/chunk-<n>-brief.md;
write your report to working/pending/XX-nnn/chunk-<n>-report.md.
```

## 3. Returns

- **The call count is the harness's** (the completion notice's `tool_uses`), never the report's [PF-541]; a DONE past the agent's budget is recorded OVER BUDGET [PF-537].
- **BLOCKED** goes to the owner as one AskUserQuestion; resume the same subagent with SendMessage.
- **OVER BUDGET** is resumed the same way with what is left and 40 more calls, unless its context is past about 150k: then a fresh chunk finishes it from `chunk-<n>b-brief.md` (the brief, headed by what is left, and the report's "Not done") [PF-534]. A chunk needing more was planned too large; the handover says so.
- **Check each chunk before the next:** `git status --short` and `git diff --stat` against its files, and its "Not done", which becomes the next brief's deviations. A defect goes back to the same subagent below about 120k of its context; past that, a fresh chunk takes a brief of the fix alone [PF-553].
- Commit each chunk's work as `XX-nnn Name: <what it does>`, the report's judgments as the body's bullets.

## 4. Then

The whole verification of `SKILL.md` step 4 runs on the manager's context, then `handover.md` and `close.md`. A failure inside one chunk's files goes back to its subagent; one across chunks is the manager's. The handover gives a line: `Dispatch: <n> chunks, models <per chunk>, calls <n/n/n>, found after the reports <count, each by who found it>`.
