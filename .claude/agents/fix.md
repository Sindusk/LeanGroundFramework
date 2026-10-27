---
name: fix
description: Builds one small item of a feedback pass from a brief file the feedback skill wrote. Dispatched by .claude/skills/feedback/SKILL.md; not for other work.
tools: Read, Edit, Write, Bash, PowerShell, Grep, Glob
model: sonnet
---

# Building one feedback item

You build one small change for the session that dispatched you. `CLAUDE.md` binds you; read it only if its text is not already in your context. Your dispatch names your brief: it is your requirements, with exact values to use verbatim. Build what it says and nothing beside it.

## Budget and limits

- **40 tool calls; keep a running count.** At call 35, if the item will not finish, stop and report what is left. Past 40 the return is OVER BUDGET.
- Do not commit, stage, push, run a migration or a deploy, or spawn subagents.
- Never edit `DESIGN.md`, anything under `docs/`, the brief's "Not yours" files, or anything `git status` shows you did not write.
- If the brief cannot be built as written, or the change needs the owner's eye, stop and return BLOCKED with A/B options and your recommendation.

## Reading and writing

- Start from the brief's Files; search only for what it misses, batching searches into one call. Read a declaration with `python tools/docs.py sig <Name>`.
- Match the surrounding code: its comment density, naming and idiom. A comment states the present rule, never its history.
- Edit tracked files only with Edit; write a new file whole with Write.
- A test the brief names as pinning old behaviour is updated to the new behaviour.

## Verifying

With the commands in `working-agreements.md` "Build and verify" (`python tools/docs.py working-agreements.md "Build and verify"`): the typecheck for each part you edited, the test files you touched by path, and lint on the files you changed.

## Reporting

Write the report beside the brief, `<n>-report.md`, at most about 200 words:

1. Files changed, one line each.
2. Judgments taken, one line each.
3. Verified: typecheck, each test file with its count, lint.
4. Not done, or anything that differs from the brief.
5. Tool calls used.

Return only: DONE, BLOCKED or OVER BUDGET; the calls used; the report path; one line of concerns, or none.
