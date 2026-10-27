# bootstrap: the interview

Two parts, in one turn each. Answers may be short; "you pick" is an answer, and the recommendation is then written and listed as a default in the summary.

## 1. Free text, in one message

Ask these as a numbered list the owner answers by number. Skip any the conversation already answered, and say what you took from it instead.

1. **The project:** its name, and a paragraph on what it is, who it is for, and what using it is like at its best. (→ `DESIGN.md` 1, `CLAUDE.md`, `README.md`)
2. **Pillars and non-goals:** the three to six principles that settle arguments, and what the first release will not do. (→ 1)
3. **Constraints:** licences, another product to stay clean of, platforms, privacy, a public repository, external services and their limits, saved data that must survive. (→ 2, `CLAUDE.md` "Always")
4. **Stack:** language, framework, build and test tools, storage, where it runs; or "you pick". (→ 3, `leanground.json`, "Build and verify")
5. **Systems:** the parts as the owner sees them, a sentence each. (→ 4)
6. **Initiatives:** the first things a user or the owner should notice, in the order wanted. (→ `LEDGER.md` Undesigned)
7. **Data, budgets, look:** where data lives; speed, size or cost limits; the visual direction and voice. (→ 5, 7, 9)
8. **Risks:** what could sink it, and what would show it happening. (→ 10)
9. **Running and checking it:** how the owner runs the app, ports, accounts or seed data, a dev server they keep open. (→ "Manual checks")
10. **Working with agents:** anything the owner already knows they want or hate, in their own words. (→ "Owner preferences", dated)

## 2. Choices, in one AskUserQuestion

Up to four questions, recommendation first:

- **ID prefix:** two or three capitals from the project's name (recommended), or the owner's own.
- **Commits:** commit and push without asking at each checkpoint (recommended); commit without pushing; ask before each commit.
- **Collaborators:** none (recommended), or a named person who answers design questions with their own agent.
- **Commit bodies:** optional (recommended), or required on every commit.

The owner's name as the documents should say it, and the branch (`main` unless named), come from the conversation or git config; ask only if neither says.
