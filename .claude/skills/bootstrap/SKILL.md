---
name: bootstrap
description: Turn a fresh copy of the Baseline kit into this project's own — interview the owner, fill DESIGN.md, LEDGER.md, CLAUDE.md, the agent notes and tools/baseline.json, set up git and its hooks, and make the first commit. Use when tools/baseline.json says "bootstrapped": false, or the owner says "bootstrap", "set up the project" or "start a new project".
argument-hint: "[a pitch, or the path of existing code to adopt]"
---

# bootstrap

Run once per project, in a session of its own. The kit's documents hold `{{PROJECT}}`, `{{PREFIX}}`, `{{OWNER}}` and `{{BRANCH}}` placeholders and `<!-- bootstrap: … -->` comments saying what belongs in each spot; this skill fills every one, then deletes the comment. `BASELINE.md` explains the kit. The skeletons are small, so this is the one task that reads `DESIGN.md` and `LEDGER.md` whole; every later task reads them by block.

**What is invented and what is asked.** The owner's words fill the documents; where they leave a gap, write the recommendation only for routine detail and say so in the summary. A real design choice is never invented: it becomes a numbered question in `DESIGN.md` 6.2 (step 4), for the first design round.

## 1. Where things stand (one call)

If the folder is not a git repository, `git init -b main` first (`git branch -m <name>` later if the owner names another branch); `tools/docs.py` reads only a repository's files. Then `git config core.hooksPath .githooks; git status --short; git log --oneline -3; python tools/docs.py check` and a listing of the top-level folders. Decide which case this is:

- **New:** no source code yet. Follow every step.
- **Adopting existing code:** the kit was copied into a codebase that already exists. Follow every step, and `adopt.md` where step 3 says. If the owner keeps a machine-wide ports file in another project (PORTS.md), copy it in and claim the project's ports in it.

## 2. Interview

Follow `interview.md`: one message of free-text questions, then one AskUserQuestion for the choices. Write nothing before the answers come back.

## 3. Fill the documents

Edit each file with the Edit tool (`replace_all` for a placeholder), never the shell. In this order, so each later file can cite the earlier:

1. **`tools/baseline.json`:** `project`, `prefix`, `owner`, `collaborators`, `branch`, `push_on_commit`, `shell`, `source_roots`, the `commands` (`BASELINE.md` "Settings" says what each means), `commit_body`. Leave `bootstrapped` false until step 6.
2. **`DESIGN.md`:** the title line, sections 1 to 3; one `### 4.n` heading per system with a paragraph of intent; 5 and 7 to 10 ("None yet." where the owner has nothing); 6.5's first release if named. Section numbers 1 to 11 never change: tools and agents cite them. Contents: `python tools/docs.py toc DESIGN.md`.
3. **`LEDGER.md`:** one Undesigned line and one `### Name` block per Initiative the owner named, each block a paragraph of intent with the sections it touches; the Contents from `toc LEDGER.md`. The next package ID stays 100.
4. **`CLAUDE.md`:** the opening paragraph and the project's own "Always" rules, each citing its section. Keep it within its budget (`python tools/docs.py budget`); detail goes to `working-agreements.md`, which `CLAUDE.md` routes to.
5. **`docs/agent-notes/working-agreements.md`:** "Writing documents", "Shell and editing", "Build and verify" (each command, quietly filtered, and the test layers), "Manual checks", "Owner preferences".
6. **`docs/agent-notes/where-things-live.md`:** "Wiring", "Layers" and "Debug commands" from the stack, each line marked "(planned)" until code exists; "Systems" stays "None yet." for a new project (`adopt.md` for existing code).
7. **`design-questions.md`:** the glossary, one term per project word a reader outside the project would not know.
8. **Permissions:** don't edit `.claude/settings.json` (it governs the agent's own permissions, so its edit is the owner's). Give the owner, in the summary, a `permissions.allow` list for the build and test commands to add there.
9. **`README.md`:** a short one for people: what the project is, how to run it, and that `CLAUDE.md` is where agents start. Files the constraints call for: a `LICENSE` for a named licence, `.gitignore` entries for local data (databases, caches, secrets).
10. **The rest:** `git grep -n -e "{{" -e "<!-- bootstrap:" -- ":!.claude" ":!tools" ":!BASELINE.md"` lists every placeholder and comment left; fill each.

## 4. Raise the open choices

Write every design choice the interview left open as drafts, one per topic (`## Questions: DESIGN.md <topic>`, `- **G1.** …` items, each with candidates, a recommendation and the cost of being wrong), and run `python tools/docs.py raise <draft>` for each. Name each Initiative's questions on its ledger line ("its design round: questions 1 to 4").

## 5. The first history row

`| <date> | The project's design baseline: vision, constraints, foundation and systems (1, 2, 3, 4) | Set from the owner's interview at bootstrap |` through `python tools/docs.py history add <file>`.

## 6. Verify and commit

1. Set `"bootstrapped": true` in `tools/baseline.json`.
2. `python tools/docs.py check` must pass: every placeholder and bootstrap comment is gone, every citation resolves, every budget holds.
3. `python -m unittest tools/test_docs.py tools/test_hooks.py`.
4. Show the owner a summary: the systems and Initiatives written, the questions raised by number, the defaults chosen, and the permissions to add (step 3.8). Commit `Bootstrap <project> from the Baseline kit` with the trailer `CLAUDE.md` names; push only if a remote exists and `push_on_commit` is set.

Then stop: the next session is the first design round (the design skill) for the Initiative wanted first.
