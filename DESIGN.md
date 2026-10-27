# {{PROJECT}} — Design Document

<!-- bootstrap: one italic line: what the project is in a sentence, and its identifiers. -->

This document states what is true. In section 4, each system's **Built rules** subsection is what the code does now; the rest of its section is the planned design, which is intent, not evidence that anything exists. Rule text states the present rule; where this document and the code disagree, reconcile them deliberately.

- **Why** a rule is what it is: `design-history.md`. It carries no requirements; where it disagrees with this document, this document wins.
- **Open design questions** are cited by permanent number (question 12) and live in section 6.2, with the idea backlog. **Open tuning questions** are section 11.
- **The roadmap** is section 6: Initiatives and their Work Packages. Where each stands is in one ledger, `LEDGER.md` at the root.
- Agents read one section at a time (`python tools/docs.py 4.2`), never this whole file.

---

## Contents

- [1. Vision](#1-vision)
- [2. Constraints](#2-constraints)
- [3. Technical Foundation](#3-technical-foundation)
- [4. Systems](#4-systems)
- [5. Data Layout](#5-data-layout)
- [6. Roadmap](#6-roadmap)
  - [6.1 Ledger](#61-ledger)
  - [6.2 Open Design Questions](#62-open-design-questions)
  - [6.3 Initiatives](#63-initiatives)
  - [6.4 Delivered](#64-delivered)
  - [6.5 Releases](#65-releases)
  - [6.6 Acceptance Criteria](#66-acceptance-criteria)
  - [6.7 Known Issues](#67-known-issues)
- [7. Performance Budget](#7-performance-budget)
- [8. Interfaces and API](#8-interfaces-and-api)
- [9. Presentation](#9-presentation)
- [10. Risks](#10-risks)
- [11. Open Tuning Questions](#11-open-tuning-questions)

## 1. Vision

<!-- bootstrap: two or three short paragraphs: what the project is, who it is for, and what using it is like at its best. Concrete nouns, no marketing. -->

**Pillars**

<!-- bootstrap: three to six pillars, each a bold phrase and one sentence, as `- **1.** **Phrase.** Sentence.` Pillars settle arguments: each should rule something out. -->

**Non-goals (v1):** <!-- bootstrap: what this project deliberately won't do in its first release. -->

## 2. Constraints

The boundaries every design and build stays inside, whatever an Initiative wants.

<!-- bootstrap: one bullet per constraint that applies, deleting the rest: legal and licensing (clean-room rules against another product, licences of dependencies and assets, where attribution is recorded); platforms and compatibility targets; privacy and data handling; public-repository rules (no hosts, logins, keys or personal data in tracked files); external services and their rate limits; compatibility with saved data before release (normally none: old data is discarded or refunded, and no migration is designed). -->

## 3. Technical Foundation

<!-- bootstrap: language and version, framework, build tool, test frameworks and how tests are layered (unit, integration, end to end), persistence, deployment target, and the layering rule the code keeps (for example, "core/ stays free of framework imports, enforced by a test"). -->

## 4. Systems

Each system is a `### 4.n` subsection: its planned design, then, once anything of it is built, a `#### 4.n.1 Built rules` subsection stating exactly what the code does (keys, defaults, ranges, messages, edge cases, the debug controls). A package's rules are written there before its code; when code makes a Built rule false, the rule is updated in the same change.

<!-- bootstrap: one `### 4.n Name` heading per system the interview named, each with a paragraph of intent and the questions it raises (as numbered questions in 6.2). No Built rules until something is built. Add each heading to Contents. -->

## 5. Data Layout

<!-- bootstrap: where data lives (files and folders, schemas, database tables), how it is versioned, and what is reloaded when (the reload contract). -->

## 6. Roadmap

This is the only roadmap. It says what is happening and what comes next; it is not the record of finished work, which goes to `docs/archive/`, and lasting rules live in sections 1 to 5 and 7 to 10.

- An **Initiative** is a change the owner or a user would notice: a new system, a rework of one, or a release-sized piece of content. If it would not earn a sentence in a changelog, it is not an Initiative. Its name is its identity and promises nothing about order.
- A **Work Package** is a buildable component of an Initiative, built and reviewed on its own. It has a permanent `{{PREFIX}}-` number that never changes and is never reused. A package holds at most an unnumbered checklist; anything needing its own review becomes a peer package, never a suffix, a stage or a nested package. An Initiative is cut into packages only once it is Work-Ready. The owner may place a package outside any Initiative (a standalone package).
- **Everything else is just work:** documentation, tooling, cleanups, fixes, verification passes. It gets no ID and no ledger line; the commit is the record.
- A **Release** groups the Initiatives that must land together before a release boundary (6.5). Membership changes without renaming anything.

The ledger, `LEDGER.md` at the root, groups work by **how actionable it is**, not by when it will happen. Where an item stands is written on its ledger line and nowhere else. How a package becomes buildable, who decides what, and how IDs are claimed are in `docs/agent-notes/working-agreements.md`.

### 6.1 Ledger

The ledger is the top of `LEDGER.md` at the root, kept apart from this document so the owner can read it alone; the Initiatives' blocks follow it there (6.3). This heading stays so the sections after it keep their numbers.

### 6.2 Open Design Questions

The design decisions still open, and the idea backlog. **Nothing here is a rule**: an answered question's rule goes into the design and its reason into `design-history.md`. Numeric tuning questions are section 11, not here.

**Question numbers are permanent.** The design and its history cite questions by number (question 12), so a number is never reused or renumbered. A new question takes the next free number: **1**.

**How a question runs.** A question is a numbered item: the gap and where the design is silent, the candidates **(a)**, **(b)** where there are any, where it was found, then a **Recommendation:** with its tradeoff and the **Cost of being wrong:**. When the owner or a collaborator answers, the answer is written under the question as `> **Decision (date, name):**`, naming who decided: the rule as decided, whether it overrules the recommendation and why, what is unverified, and "Not yet consolidated". Consolidation is a separate pass the owner asks for, usually covering several decided questions: the rule goes into the design, the reason into `design-history.md`, and the question is removed. A question belonging to an Initiative with a working document is asked there instead, with a note here naming the document and the numbers.

**Open questions**

None yet.

**Idea backlog**

Pitches not yet adopted, each a bold letter and a sentence (`- **A.** ...`), so a pitch is cited as "pitch A". A pitch adopted as an Initiative is removed here and goes on the ledger as Undesigned.

None yet.

### 6.3 Initiatives

The Initiatives and their Work Packages are in `LEDGER.md`, under its Initiatives heading, below the ledger: each block states the Initiative's intent, where its design lives, what it depends on and, once it is cut, its packages. Read one with `python tools/docs.py {{PREFIX}}-nnn` or `python tools/docs.py "<Initiative>"`.

### 6.4 Delivered

One paragraph per closed Initiative, newest last: what a user now has, in one sentence of clauses; the sections holding its rules; what was left open and where it went. Its delivery record is in `docs/archive/initiatives/`.

None yet.

### 6.5 Releases

Review checkpoints, not promises. Each Release is a bullet: its name in bold, what a user can do at its end, the evidence that it worked, and the Initiatives in it.

<!-- bootstrap: the first release, if the owner has one in mind; else "None defined yet." -->

### 6.6 Acceptance Criteria

The questions a playtest, review or real use must answer before a Release is called done. Each is a bullet a tester could check.

None yet.

### 6.7 Known Issues

Loose ends found while building and not fixed in their session: code TODOs, harmless warnings, documentation that disagrees with the code, checks not yet done. Each stays here until it is fixed, then its line is removed. They are just work: no ID. Design questions belong in 6.2, not here. A line found during a package ends "Found in {{PREFIX}}-nnn".

None yet.

## 7. Performance Budget

<!-- bootstrap: the budgets the code keeps (latency, frame time, memory, bundle size, per-tick work, query counts), each as a rule a reviewer can check, and how each is measured. "None yet" if the owner has none. -->

## 8. Interfaces and API

<!-- bootstrap: what other code, users or services call (public API, CLI, HTTP routes, events, file formats), and the stability promise each carries. "None yet" for a project with no outside callers. -->

## 9. Presentation

<!-- bootstrap: the look and voice: visual direction, typography, palette, text style, accessibility targets. "None yet" for a project with no user-facing surface. -->

## 10. Risks

<!-- bootstrap: the risks the owner named, each with what would show it is happening and the response. -->

## 11. Open Tuning Questions

Numbers to be settled by play, measurement or review: each a bullet naming the value, where it is used (a section), its current setting and what would decide it. Tuning questions are not numbered design questions; a tuning question that turns out to be a design choice moves to 6.2.

None yet.
