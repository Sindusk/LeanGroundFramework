# Where things live

A routing map for implementation work: where each system's code, data and docs are, and how they connect. Open the files it names; don't read the tree. `python tools/docs.py where <system>` prints one system's paragraph; `where "recipe: <kind>"` one recipe.

## Documents

- `DESIGN.md`: the design. Section 2 constraints; 3 technical foundation; 4 systems, each with a **Built rules** subsection for what the code does; 5 data layout; 6 roadmap (6.2 open design questions and idea backlog, 6.7 known issues); 7 performance budget; 8 interfaces; 9 presentation; 11 open tuning questions.
- `LEDGER.md`: the ledger, where every Initiative and Work Package stands, and the next free `{{PREFIX}}-` ID; below it, each Initiative's block with its Work Packages.
- `design-history.md`: why the design says what it does (the Decision Log).
- `design-questions.md`: design rounds waiting for the owner's answers.
- `docs/initiatives/`: Initiative working documents, when an Initiative has one.
- `docs/archive/`: delivery records and executed plans. Not authoritative.
- `docs/agent-notes/`: how to work here (index in its `README.md`).
- `tools/docs.py`: prints one block of these documents, finds code (`where`, `sig`) and checks that citations, the ledger and budgets hold; `python tools/docs.py help` lists its forms. `tools/project_docs.py`, when present, adds this project's own commands to it.
- `tools/baseline.json`: the project's settings for the kit (ID prefix, owner, commands, budgets) and the list of core files.

## Wiring (start here when adding anything)

<!-- bootstrap: the entry point and every place a new thing must be registered (routes, registries, dependency injection, config, migrations), one bullet each as `- path: what is registered there.`, from the stack, each marked "(planned)" until the package that writes it removes the mark. -->

## Layers

<!-- bootstrap: the layers from DESIGN.md 3 and where each lives: pure logic, the framework layer, the public API, tests (and which layer each kind of test exercises), generated files. -->

## Systems

One paragraph per system, bold name first with its `DESIGN.md` section in brackets, then: its pure logic, its framework layer, its API, its tests, its data and its debug controls, each as paths and class or module names. A package that adds to a system updates its paragraph in the same change.

None yet.

## Recipes for common additions

Each recipe is the files to touch for one kind of addition, in order, numbered, with an example to copy: `**Recipe: <kind>.** (1) … (2) …`. A recipe is written the second time a kind of addition is made, from the two examples, and a package uses it instead of a past package's diff. Imports go in the same edit as their first use, or before it.

None yet.

## Debug commands

<!-- bootstrap: where debug commands or controls live and how they are registered. A debug command never needs coordinates or ids the tester must look up: it targets what is selected, looked at or nearest. -->
