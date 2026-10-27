# {{PROJECT}} — Ledger

One line per item: its name, then where it stands. Details live in the item's block under Initiatives, below the ledger; search for its name. The open questions a line names are in `DESIGN.md` 6.2. A `{{PREFIX}}-` line under an Initiative is one of its Work Packages, and a path under it is the file its design is being worked out in. A built package stays on its line until the owner approves it. What Initiatives and Work Packages are is in `DESIGN.md` section 6.
The next package ID is {{PREFIX}}-100.

## Contents

- [Work-Ready](#work-ready)
- [Designed](#designed)
- [Undesigned](#undesigned)
- [Initiatives](#initiatives)
  - [Standalone Work Packages](#standalone-work-packages)

## Work-Ready

The owner has placed these items here for building and package cutting. Questions found in a cut stay on the affected lines until the owner decides; this does not move an item between groups.

None yet.

## Designed

The shape is decided. What follows the dash stands between the item and Work-Ready.

None yet.

## Undesigned

A name and an intention. Needs a design round before anything else.

<!-- bootstrap: one line per Initiative the interview named, `- **Name** — its design round`, each with a block under Initiatives below. -->

## Initiatives

Each block states the Initiative's intent, where its design lives, and what it depends on, then its Work Packages once it is cut. Its standing is on its ledger line only. Agents read one block with `python tools/docs.py {{PREFIX}}-nnn` or `python tools/docs.py "<Initiative>"`, not this whole file.

<!-- bootstrap: a `### Name` block per Undesigned line above: a paragraph of intent, the DESIGN.md sections it will touch, what it depends on. Add each heading to Contents, above Standalone Work Packages. -->

### Standalone Work Packages

Packages the owner placed outside any Initiative. Each block has the same parts as a package inside one. None is open.
