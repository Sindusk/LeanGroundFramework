# bootstrap: adopting existing code

When the kit is copied into a codebase that already exists, the documents must describe the code as it is, without reading all of it into this session.

1. **Map the systems with subagents.** One Explore agent per top-level source folder (or group of small ones), `model: "haiku"` for a plain listing, `"sonnet"` where judgement is needed, run in parallel. Each returns at most 300 words: the systems the folder holds, each with its entry points, main files and tests as paths, how a new thing is registered, and the commands that build and test it. Never ask for code or file bodies.
2. **`where-things-live.md`:** "Wiring" and "Layers" from the reports; one "Systems" paragraph per system, bold name first with its `DESIGN.md` section, then its paths.
3. **`DESIGN.md` 4:** a `### 4.n` heading per system with a paragraph of what it does today. Write a **Built rules** subsection only for behaviour read from the code and checked (a test, a run, or the code itself, cited); for the rest add one 6.7 line per system: "<system>'s Built rules are not written yet; the first package that changes it writes the rules it touches."
4. **Ledger:** work already under way that the owner wants tracked becomes Undesigned or Designed lines like any Initiative. Nothing already built gets a package id.
5. **The first history row** says the design was written from the existing code at the commit adopted (`git rev-parse --short HEAD`).
6. **Existing agent files:** an older `CLAUDE.md`, `AGENTS.md` or agent notes are read once; each rule worth keeping moves to the document the kit gives it, and the old file is removed in the same commit, so no copy drifts.
