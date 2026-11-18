"""Upgrades a project's core files to a newer copy of the Lean Ground Framework (the kit): a plan first, then the
copies, so no agent retypes the kit's files through Write.

    python tools/upgrade.py <kit folder> [--apply] [--base <commit>] [--theirs <path>] ... [--ours <path>] ...
                            [--remove] [<path> ...]

Run from the project being upgraded, pointed at a local checkout of the kit (no network). Without --apply it prints
the plan and changes nothing. Naming paths limits the run to those core files (a file, or a folder ending in /);
name tools/leanground.json to include the settings, which a limited run otherwise leaves alone.

Every file in the kit's "core" list (its tools/leanground.json) is compared with the project's file at the same path,
or at the path "core_paths" in the project's tools/leanground.json maps it to, prefix to prefix
({".claude/skills/lg-package/": ".claude/skills/mm-package/"}). A kit skill folder missing here, unmapped, while the
project has one of the same name under another prefix, is held back and the mapping proposed, never copied twice.
Each file is:
  identical       nothing to do (line endings and mapped skill names aside);
  new             absent here: added;
  replace         changed in the kit, unedited here: replaced;
  kept            edited here, unchanged in the kit: left alone;
  conflict        changed in the kit and edited here: left alone unless named with --theirs (take the kit's copy);
                  --ours keeps the project's and counts it resolved. The plan gives both sides' change sizes and
                  the git diff --no-index command that shows them;
  not in the kit  under the project's old core list, gone from the kit: reported; --remove deletes it only when the
                  base shows the kit had it and the project left it unedited.
"Edited here" compares the project's file with the kit's copy at the commit the project last took: "kit_version" in
the project's tools/leanground.json, or --base <commit>, looked up with git in the kit checkout (renamed kit paths
through PATH_RENAMES). With neither, every file that differs is a possible conflict, treated as a conflict.

A copied file has the kit's skill names rewritten to the project's through the same mapping (lg-package to
mm-package); a plain-word name (bootstrap) is rewritten only where it names a skill: the name: field, a heading,
a skills/<name>/ path and "the <name> skill". The plan prints the count per file.

Settings: tools/leanground.json is never replaced. The plan lists keys the kit has and the project lacks (with the
kit's default, or the project's value under an old name from SETTING_RENAMES), keys the kit lacks, missing "core"
and "budgets" entries (mapped), and budgets that differ (never changed). --apply adds only what is missing, in the
kit's order, keeping the file's indent.

--apply refuses, changing nothing, when any file it would write has uncommitted changes (so git checkout -- <path>
undoes it), when the project is not a git repository or has no tools/leanground.json, when the kit is the project
itself, or when the kit holds no tools/leanground.json with a "core" list. Files are written with the kit's bytes,
staged beside the target and swapped in; an executable kit file (.githooks/*) is made executable where the platform
allows, and the plan names the git add --chmod=+x to run where it does not. After a full apply that leaves nothing
unresolved it records "kit_version": the kit's commit, or a hash of its core files when the kit is not a clean git
checkout (which a later run cannot use as a base). Then it runs python tools/docs.py check and
python -m unittest discover -s tools in the project and reports both; it never rolls back, never commits, and never
touches a file outside the kit's core list but tools/leanground.json. The last line says what to do next.

Exit codes: 0 a dry run, nothing to do, or applied cleanly; 1 refused, nothing changed; 2 applied, but conflicts
remain or the check or the tests failed (it says which). Standard library only.
"""

import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

USAGE = ("Usage: python tools/upgrade.py <kit folder> [--apply] [--base <commit>] [--theirs <path>] ..."
         " [--ours <path>] ... [--remove] [<path> ...]")
SETTINGS = "tools/leanground.json"
SKILLS = ".claude/skills/"
# The kit's own renames, old name to current: settings a project may still hold, and paths an old kit commit used.
SETTING_RENAMES = {"subagent_build_past": "handoff_past"}
PATH_RENAMES = {".claude/skills/package/": ".claude/skills/lg-package/",
                ".claude/skills/design/": ".claude/skills/lg-design/",
                ".claude/skills/feedback/": ".claude/skills/lg-feedback/",
                ".claude/skills/bootstrap/": ".claude/skills/lg-bootstrap/"}
CONFLICTS = ("conflict", "possible")


class Refused(Exception):
    pass


def git(repo, *args):
    """Runs git in repo with literal pathspecs; returns the completed process, its output as bytes."""
    return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                          env=dict(os.environ, GIT_LITERAL_PATHSPECS="1"))


def out(process):
    return process.stdout.decode("utf-8", "replace")


def is_checkout(folder):
    top = git(folder, "rev-parse", "--show-toplevel")
    return top.returncode == 0 and Path(out(top).strip()).resolve() == Path(folder).resolve()


def parse(argv):
    options = {"kit": None, "apply": False, "base": None, "theirs": [], "ours": [], "remove": False, "paths": []}
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg in ("--apply", "--remove"):
            options[arg[2:]] = True
        elif arg in ("--base", "--theirs", "--ours"):
            if not args:
                raise Refused(f"{arg} needs a value. {USAGE}")
            value = args.pop(0)
            if arg == "--base":
                options["base"] = value
            else:
                options[arg[2:]].append(slashed(value))
        elif arg.startswith("--"):
            raise Refused(f"{arg!r} is not understood here. {USAGE}")
        elif options["kit"] is None:
            options["kit"] = arg
        else:
            options["paths"].append(slashed(arg))
    if options["kit"] is None:
        raise Refused(f"Name the newer copy of the kit. {USAGE}")
    return options


def slashed(name):
    name = name.replace("\\", "/")
    return name[2:] if name.startswith("./") else name


def load(path):
    """The JSON object in path, or None when the file is missing; Refused when it does not parse."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        value = json.loads(text)
    except ValueError as error:
        raise Refused(f"{path} is not valid JSON: {error}")
    return value if isinstance(value, dict) else None


def files_under(root, entries, tracked):
    """Every file under the core entries (a file, or a folder ending in /), relative and / separated."""
    if not entries:
        return []
    if tracked:
        names = out(git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *entries))
        found = [name for name in names.split("\0") if name]
    else:
        found = []
        for entry in entries:
            path = root / entry
            if entry.endswith("/") and path.is_dir():
                found += [p.relative_to(root).as_posix() for p in sorted(path.rglob("*")) if p.is_file()]
            elif path.is_file():
                found.append(entry)
    return [name for name in dict.fromkeys(found)
            if (root / name).is_file() and "__pycache__" not in name.split("/") and not name.endswith(".pyc")]


def modes(root, files, tracked):
    """The files git or the file system holds executable."""
    if tracked and files:
        listed = out(git(root, "ls-files", "-s", "-z", "--", *files)).split("\0")
        return {line.split("\t", 1)[1] for line in listed if line.startswith("100755")}
    return {name for name in files if os.name != "nt" and os.access(root / name, os.X_OK)}


def mapped(path, mapping):
    """path under the longest mapped prefix it starts with, or path itself."""
    for old, new in sorted(mapping.items(), key=lambda pair: -len(pair[0])):
        if path == old or (old.endswith("/") and path.startswith(old)):
            return new + path[len(old):]
    return path


def skill_of(prefix):
    match = re.fullmatch(r"\.claude/skills/([^/]+)/", prefix)
    return match.group(1) if match else None


def skill_names(mapping):
    """Skill name to skill name, from the mapping's skill folders."""
    names = {}
    for old, new in mapping.items():
        if skill_of(old) and skill_of(new) and skill_of(old) != skill_of(new):
            names[skill_of(old)] = skill_of(new)
    return names


def rename_skills(text, names):
    """text with each skill name in names rewritten, in one pass; returns (text, how many). A hyphenated name is
    distinctive and rewritten wherever it stands whole (not inside lg-packages or lg-package-x); a plain word only
    where it names a skill: the name: field, a heading, a skills/<name>/ path and "the <name> skill"."""
    spans = []
    for old, new in names.items():
        name = re.escape(old)
        if "-" in old:
            patterns = [rf"(?<![\w-])({name})(?![\w]|-\w)"]
        else:
            patterns = [rf"(?m)^name:[ \t]*({name})[ \t]*\r?$", rf"(?m)^#+[ \t]+({name})(?=:|[ \t]*\r?$)",
                        rf"skills/({name})/", rf"\b[Tt]he ({name}) skill\b"]
        for pattern in patterns:
            spans += [(match.start(1), match.end(1), new) for match in re.finditer(pattern, text)]
    result, at, count = [], 0, 0
    for start, end, new in sorted(spans):
        if start < at:
            continue
        result += [text[at:start], new]
        at, count = end, count + 1
    return "".join(result) + text[at:], count


def rewritten(data, names):
    """data's bytes with skill names rewritten when it is UTF-8 text; returns (bytes, how many)."""
    if not names:
        return data, 0
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data, 0
    text, count = rename_skills(text, names)
    return text.encode("utf-8"), count


def normal(data, names):
    """Bytes as compared: LF line ends, skill names under the kit's current names."""
    return rewritten(data.replace(b"\r\n", b"\n"), names)[0]


def change(old, new):
    """Lines added and removed from old to new, as "+a -r"."""
    added = removed = 0
    old_lines = old.decode("utf-8", "replace").splitlines()
    new_lines = new.decode("utf-8", "replace").splitlines()
    for line in difflib.unified_diff(old_lines, new_lines, n=0, lineterm=""):
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return f"+{added} -{removed}"


class Kit:
    def __init__(self, folder):
        self.root = Path(folder).resolve()
        config = load(self.root / SETTINGS) if self.root.is_dir() else None
        if not config or not isinstance(config.get("core"), list) or not config["core"]:
            raise Refused(f"{folder} holds no {SETTINGS} with a \"core\" list; point at a checkout of the kit")
        self.config = config
        self.entries = [entry for entry in config["core"] if isinstance(entry, str)]
        self.tracked = is_checkout(self.root)
        self.files = files_under(self.root, self.entries, self.tracked)
        self.executable = modes(self.root, self.files, self.tracked)
        self.version, self.warning = self.identify()

    def identify(self):
        """The kit's commit when its core files are as committed, else a hash of them, with a warning."""
        warning = None
        if self.tracked:
            head = git(self.root, "rev-parse", "--verify", "-q", "HEAD")
            dirty = out(git(self.root, "status", "--porcelain", "--", *self.entries)).splitlines()
            if head.returncode == 0 and not dirty:
                return out(head).strip(), None
            shown = ", ".join(line[3:] for line in dirty[:4]) + (", …" if len(dirty) > 4 else "")
            warning = (f"the kit has uncommitted changes in its core files ({shown}): this run uses its working tree,"
                       " and the version it records is a hash of those files, which a later run cannot use as a base")
        digest = hashlib.sha256()
        for name in sorted(self.files):
            digest.update(name.encode("utf-8") + b"\0" + normal((self.root / name).read_bytes(), {}) + b"\0")
        return "sha256:" + digest.hexdigest()[:16], warning

    def commit(self, name):
        """The full hash of a commit the kit checkout holds, or None."""
        if not self.tracked or not name or name.startswith("sha256:"):
            return None
        found = git(self.root, "rev-parse", "--verify", "-q", f"{name}^{{commit}}")
        return out(found).strip() if found.returncode == 0 else None

    def at(self, commit, path):
        """The kit's copy of path at commit, under its current or an older name, or None."""
        candidates = [path] + [old + path[len(new):] for old, new in PATH_RENAMES.items() if path.startswith(new)]
        for candidate in candidates:
            shown = git(self.root, "show", f"{commit}:{candidate}")
            if shown.returncode == 0:
                return shown.stdout
        return None


class Item:
    def __init__(self, kind, kit_path, target, note="", names=0, data=None):
        self.kind, self.kit_path, self.target, self.note, self.names, self.data = (kind, kit_path, target, note,
                                                                                    names, data)

    def matches(self, name):
        name = name.rstrip("/")
        return any(path == name or path.startswith(name + "/") for path in (self.kit_path, self.target) if path)


def held_skills(kit, project, mapping, project_core):
    """Kit skill folders missing here and unmapped, with the project's folders they were likely renamed to."""
    held = {}
    have = project / SKILLS
    folders = sorted(p.name for p in have.iterdir() if p.is_dir()) if have.is_dir() else []
    for entry in kit.entries:
        name = skill_of(entry)
        if not name or mapped(entry, mapping) != entry or (project / entry).is_dir():
            continue
        bare = name[3:] if name.startswith("lg-") else name
        found = [f for f in folders if f != name and (f == bare or f.endswith("-" + bare))]
        listed = [f for f in found if f"{SKILLS}{f}/" in project_core]
        if found:
            held[entry] = [f"{SKILLS}{f}/" for f in (listed or found)]
    return held


def classify(kit, project, mapping, base, held):
    """One Item per kit core file."""
    forward, backward = skill_names(mapping), {new: old for old, new in skill_names(mapping).items()}
    renamed_then = {skill_of(old): skill_of(new) for old, new in PATH_RENAMES.items()}
    items = []
    for name in kit.files:
        target = mapped(name, mapping)
        if any(name.startswith(entry) for entry in held):
            items.append(Item("held", name, target))
            continue
        theirs = (kit.root / name).read_bytes()
        data, count = rewritten(theirs, forward)
        path = project / target
        ours = path.read_bytes() if path.is_file() else None
        then = kit.at(base, name) if base else None
        if ours is None:
            kind = "conflict" if then is not None else "new"
            note = "removed here, still in the kit" if then is not None else ""
            items.append(Item(kind, name, target, note, count, data))
            continue
        kit_text, our_text = normal(theirs, {}), normal(ours, backward)
        if our_text == kit_text:
            items.append(Item("identical", name, target))
            continue
        if base is None:
            note = f"differs from the kit by {change(our_text, kit_text)}"
            items.append(Item("possible", name, target, note, count, data))
            continue
        then_text = normal(then, renamed_then) if then is not None else None
        if then_text == our_text:
            items.append(Item("replace", name, target, "", count, data))
        elif then_text == kit_text:
            items.append(Item("kept", name, target))
        else:
            sides = (f"the kit {change(then_text, kit_text)} and the project {change(then_text, our_text)} since"
                     f" {base[:7]}" if then_text is not None else
                     f"new in the kit since {base[:7]} but already here, {change(our_text, kit_text)}")
            items.append(Item("conflict", name, target, sides, count, data))
    return items


def leftovers(kit, project, mapping, base, project_core, items, held, tracked):
    """Project files under its old core list or a mapped core folder that no kit file maps to, outside the folders
    a held kit skill is likely to map to."""
    targets = {item.target for item in items} | {SETTINGS}
    entries = [entry for entry in project_core if isinstance(entry, str)]
    entries += [mapped(entry, mapping) for entry in kit.entries if entry.endswith("/")]
    waiting = [folder for folders in held.values() for folder in folders]
    backward = {new: old for old, new in mapping.items()}
    found = []
    for name in files_under(project, list(dict.fromkeys(entries)), tracked):
        if name in targets or any(name.startswith(folder) for folder in waiting):
            continue
        kit_path = mapped(name, backward)
        then = kit.at(base, kit_path) if base else None
        if base is None:
            found.append(Item("unknown", kit_path, name, "removed by the kit or the project's own; no base to tell"))
        elif then is None:
            continue
        elif normal(then, {}) == normal((project / name).read_bytes(), {}):
            found.append(Item("gone", kit_path, name, "the kit dropped it; unedited here"))
        else:
            found.append(Item("gone-edited", kit_path, name, "the kit dropped it; edited here, so never removed"))
    return found


def insert_after(mapping, anchor, key, value):
    """A copy of mapping with key added after anchor, or first when anchor is None."""
    pairs = list(mapping.items())
    at = 0 if anchor is None else [k for k, _ in pairs].index(anchor) + 1
    return dict(pairs[:at] + [(key, value)] + pairs[at:])


def show(value):
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 60 else text[:57] + "…"


def merge_keys(ours, theirs, prefix, lines):
    """ours with every key of theirs it lacks, in theirs' order; nested objects merged the same way."""
    merged, previous = dict(ours), None
    for key, value in theirs.items():
        if key in merged:
            if isinstance(value, dict) and isinstance(merged[key], dict) and key not in ("budgets", "core_paths"):
                merged[key] = merge_keys(merged[key], value, f"{prefix}{key}.", lines)
        else:
            old = next((o for o, n in SETTING_RENAMES.items() if n == key and o in ours and not prefix), None)
            if old:
                value = merged[old]
                lines.append(f"  add {prefix}{key} = {show(value)}, the value of {old}, which the kit renamed;"
                             f" delete {old} by hand")
            else:
                lines.append(f"  add {prefix}{key} = {show(value)}")
            merged = insert_after(merged, previous, key, value)
        previous = key
    return merged


def merge_settings(ours, theirs, mapping, held, written, project):
    """The project's settings with what the kit adds; returns (merged, plan lines)."""
    lines = []
    merged = merge_keys(ours, {k: v for k, v in theirs.items() if k not in ("core", "budgets")}, "", lines)
    for key in ours:
        if key not in theirs:
            renamed = SETTING_RENAMES.get(key)
            lines.append(f"  not in the kit: {key}" + (f" (renamed {renamed})" if renamed else
                                                       " (the project's own, or dropped by the kit)"))
    core = list(ours.get("core", [])) if isinstance(ours.get("core"), list) else []
    wanted = [mapped(entry, mapping) for entry in theirs.get("core", []) if entry not in held]
    missing = [entry for entry in wanted if entry not in core]
    if missing:
        lines.append("  core: add " + ", ".join(missing))
    for entry in core:
        if entry not in wanted:
            lines.append(f"  core: {entry} is not in the kit's list (the project's own, or dropped by the kit)")
    budgets = dict(ours.get("budgets", {})) if isinstance(ours.get("budgets"), dict) else {}
    added, differ = [], []
    for name, value in theirs.get("budgets", {}).items():
        target = mapped(name, mapping)
        if any(name.startswith(entry) for entry in held):
            continue
        if target not in budgets:
            if (project / target).is_file() or target in written:
                budgets[target] = value
                added.append(f"{target} {value}")
        elif budgets[target] != value:
            differ.append(f"{target} here {budgets[target]}, kit {value}")
    if added:
        lines.append("  budgets: add " + "; ".join(added))
    if differ:
        lines.append("  budgets kept where the kit's differ: " + "; ".join(differ))
    if missing or "core" in ours:
        merged["core"] = core + missing
    if added or "budgets" in ours:
        merged = merged if "budgets" in merged else insert_after(merged, None, "budgets", {})
        merged["budgets"] = budgets
    return merged, lines


def settings_text(original, settings):
    """settings as JSON in the original text's indent, line ending and final newline."""
    indent = re.search(r"\n([ \t]+)\"", original)
    text = json.dumps(settings, indent=indent.group(1) if indent else 2, ensure_ascii=False)
    text += "\n" if original.endswith("\n") or not original else ""
    return text.replace("\n", "\r\n") if "\r\n" in original else text


def put(path, data):
    """Writes data beside path, then swaps it in."""
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(path.name + ".lg-upgrade")
    staged.write_bytes(data)
    os.replace(staged, path)


def run_checks(project):
    """Runs the check and the unit tests in the project; returns (name, passed, report) for each."""
    results = []
    for name, command in (("python tools/docs.py check", [sys.executable, "tools/docs.py", "check"]),
                          ("python -m unittest discover -s tools",
                           [sys.executable, "-m", "unittest", "discover", "-s", "tools"])):
        if name.endswith("check") and not (project / "tools" / "docs.py").is_file():
            results.append((name, False, "not run: the project has no tools/docs.py"))
            continue
        print(f"Running {name} …", flush=True)
        done = subprocess.run(command, cwd=project, capture_output=True, encoding="utf-8", errors="replace")
        lines = (done.stdout + done.stderr).strip().splitlines()
        if done.returncode == 0:
            results.append((name, True, (lines or ["passed"])[-1].strip()))
        else:
            results.append((name, False, f"failed (exit {done.returncode}); its last lines:\n      "
                            + "\n      ".join(lines[-12:])))
    return results


SECTIONS = (("new", "Add, new in the kit"), ("replace", "Replace, changed in the kit and unedited here"),
            ("theirs", "Take the kit's copy (--theirs)"),
            ("conflict", "Conflicts, changed in the kit and edited here (--theirs <path> takes the kit's copy,"
                         " --ours <path> keeps this one)"),
            ("possible", "Possible conflicts, no base to tell an edit here from an older kit"
                         " (--base <commit>, --theirs <path> or --ours <path>)"),
            ("ours", "Kept by --ours"), ("kept", "Kept, edited here and unchanged in the kit"),
            ("gone", "Not in the kit any more, unedited here (--remove deletes them)"),
            ("gone-edited", "Not in the kit any more, edited here"),
            ("unknown", "Under a core entry here but not in the kit"))


def main(argv, project):
    project = Path(project).resolve()
    try:
        options = parse(argv)
        if Path(options["kit"]).resolve() == project:
            raise Refused("the kit path is this project; point at a separate checkout of the kit")
        return upgrade(options, Kit(options["kit"]), project)
    except Refused as refusal:
        print(f"upgrade.py refused, nothing changed: {refusal}".rstrip(".") + ".")
        return 1


def upgrade(options, kit, project):
    apply = options["apply"]
    tracked = is_checkout(project)
    ours = load(project / SETTINGS)
    config = ours or {}
    mapping = config.get("core_paths") or {}
    if not isinstance(mapping, dict) or not all(isinstance(v, str) for v in [*mapping, *mapping.values()]):
        raise Refused(f"\"core_paths\" in {SETTINGS} must map path prefixes to path prefixes")
    project_core = config.get("core") if isinstance(config.get("core"), list) else []

    header = []
    if kit.warning:
        header.append(f"Note: {kit.warning}.")
    if ours is None:
        header.append(f"This project has no {SETTINGS}: it was not set up from the kit, so nothing marks which files"
                      " are core or records a kit version. The plan below compares the kit's core files with"
                      " whatever stands at their paths; --apply refuses until the project adopts the kit (the"
                      " lg-bootstrap skill's adopt.md).")
    base, recorded = None, config.get("kit_version") or ""
    if options["base"]:
        base = kit.commit(options["base"])
        if base is None:
            raise Refused(f"the kit checkout holds no commit {options['base']}")
        source = "--base"
    elif recorded:
        base, source = kit.commit(recorded), "the recorded kit_version"
        if base is None:
            header.append(f"The recorded kit_version {recorded} is not a commit this kit checkout holds; without"
                          " it, every file that differs from the kit is a possible conflict. Name the kit commit"
                          " the project was taken from with --base <commit>.")
    elif ours is not None:
        header.append("No kit_version is recorded: every file that differs from the kit is a possible conflict,"
                      " never replaced unless named with --theirs. Name the kit commit the project was taken from"
                      f" with --base <commit> (git -C {kit.root.as_posix()} log --format=\"%h %ad %s\").")

    held = held_skills(kit, project, mapping, project_core)
    items = classify(kit, project, mapping, base, held)
    items += leftovers(kit, project, mapping, base, project_core, items, held, tracked)
    limited = bool(options["paths"])
    if limited:
        for name in options["paths"]:
            if name != SETTINGS and not any(item.matches(name) for item in items):
                raise Refused(f"{name} is not a core file of the kit or of this project")
        items = [item for item in items if any(item.matches(name) for name in options["paths"])]
    for flag, kind in (("theirs", "theirs"), ("ours", "ours")):
        for name in options[flag]:
            chosen = [item for item in items if item.kind in CONFLICTS and item.matches(name)]
            if not chosen and not any(item.matches(name) and item.kind == kind for item in items):
                header.append(f"--{flag} {name}: no conflict there; nothing to choose.")
            for item in chosen:
                item.kind = kind
    if options["remove"]:
        for item in items:
            if item.kind == "gone":
                item.kind = "remove"

    writes = [item for item in items if item.kind in ("new", "replace", "theirs")]
    removals = [item for item in items if item.kind == "remove"]
    unresolved = [item for item in items if item.kind in CONFLICTS]
    settings_in = ours is not None and (not limited or SETTINGS in options["paths"])
    settings_lines, merged = [], None
    if settings_in:
        merged, settings_lines = merge_settings(ours, kit.config, mapping, held,
                                                {item.target for item in writes}, project)
    record = (not limited and settings_in and not unresolved and not held and recorded != kit.version)
    if record:
        merged = merged if "kit_version" in merged else insert_after(merged, None, "kit_version", "")
        merged["kit_version"] = kit.version
        settings_lines.append(f"  record kit_version = {kit.version}")
    settings_change = merged is not None and merged != ours
    if apply:
        if ours is None:
            raise Refused(f"this project has no {SETTINGS}; adopt the kit first (the lg-bootstrap skill's adopt.md)")
        if not tracked:
            raise Refused("this project is not a git repository, so an apply could not be undone with git checkout")
        paths = [item.target for item in writes + removals] + ([SETTINGS] if settings_change else [])
        dirty = out(git(project, "status", "--porcelain", "--", *paths)).splitlines() if paths else []
        if dirty:
            raise Refused("uncommitted changes in files it would write: " + ", ".join(line[3:] for line in dirty)
                          + "; commit or stash them first, so git checkout -- <path> undoes this")

    # The plan.
    mode = "apply" if apply else "dry run"
    print(f"upgrade.py: {project.name} from the kit at {kit.root.as_posix()} ({kit.version[:16]}), {mode}.")
    print(f"Base: {base[:7]} ({source})." if base else "Base: none.")
    for line in header:
        print(line)
    if held:
        proposal = {entry: folders[0] for entry, folders in held.items() if len(folders) == 1}
        print("Kit skill folders missing here, held back rather than copied under a second name:")
        for entry, folders in held.items():
            count = sum(1 for item in items if item.kind == "held" and item.kit_path.startswith(entry))
            print(f"  {entry} ({count} files): this project has " + " or ".join(folders))
        if proposal:
            print(f"  Map them in {SETTINGS}, then run again: \"core_paths\": {json.dumps(proposal)}")
    same = sum(1 for item in items if item.kind == "identical")
    if same:
        print(f"Identical: {same} files.")
    for kind, title in SECTIONS + (("remove", "Remove (--remove)"),):
        chosen = [item for item in items if item.kind == kind]
        if not chosen:
            continue
        print(f"{title}:")
        for item in chosen:
            line = f"  {item.target}" + (f" (from {item.kit_path})" if item.target != item.kit_path else "")
            line += f": {item.note}" if item.note else ""
            line += f"; {item.names} skill names rewritten" if item.names else ""
            print(line)
            if kind in CONFLICTS + ("theirs", "ours") and item.data is not None:
                print(f"    git diff --no-index -- {item.target} {(kit.root / item.kit_path).as_posix()}")
    if settings_lines:
        print(f"Settings ({SETTINGS}, never replaced):")
        for line in settings_lines:
            print(line)
    elif ours is not None and not settings_in:
        print(f"Settings: left alone by a run limited to named paths (name {SETTINGS} to include them).")
    chmod = []
    if tracked:
        # Elsewhere the apply sets the bit itself on what it writes; Windows keeps none, so git must be told.
        kinds = ("identical", "kept", "ours") + (("new", "replace", "theirs") if os.name == "nt" else ())
        for item in items:
            if item.kit_path in kit.executable and item.kind in kinds:
                if not out(git(project, "ls-files", "-s", "--", item.target)).startswith("100755"):
                    chmod.append(item.target)
    if chmod:
        print("Executable in the kit, not in this project's index; when committing, run: git add --chmod=+x "
              + " ".join(chmod))

    if not writes and not removals and not settings_change:
        if unresolved or held:
            print(f"Nothing to apply until {len(unresolved)} conflicts and {len(held)} held skill folders are"
                  " resolved: --theirs, --ours, --base, or a core_paths mapping.")
            return 0 if not apply else 2
        print("Nothing to do: the project's core files and settings match the kit.")
        return 0
    if not apply:
        again = f"python tools/upgrade.py {options['kit']} --apply" + (f" --base {options['base']}"
                                                                       if options["base"] else "")
        print(f"Dry run: nothing changed. Next: review the plan, then run {again} with the same choices.")
        return 0

    # The apply, its refusals already passed.
    for item in writes:
        target = project / item.target
        put(target, item.data)
        if item.kit_path in kit.executable and os.name != "nt":
            target.chmod(target.stat().st_mode | 0o111)
    for item in removals:
        (project / item.target).unlink()
    if settings_change:
        original = (project / SETTINGS).read_bytes().decode("utf-8")
        put(project / SETTINGS, settings_text(original, merged).encode("utf-8"))
    print(f"Applied: {len(writes)} files written, {len(removals)} removed"
          + (", settings updated." if settings_change else "."))

    failed = []
    for name, passed, report in run_checks(project):
        print(f"{name}: {report}")
        if not passed:
            failed.append(name)
    if unresolved or held:
        print(f"Remaining: {len(unresolved)} conflicts and {len(held)} held skill folders, not applied; kit_version"
              " not recorded until they are resolved.")
    if failed:
        print("Failed after the apply (nothing rolled back): " + "; ".join(failed) + ".")
    print("Next: review git diff --stat, then commit (python tools/commit.py); git checkout -- <path> undoes a file.")
    return 2 if unresolved or held or failed else 0


if __name__ == "__main__":
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, encoding="utf-8")
    sys.exit(main(sys.argv[1:], top.stdout.strip() if top.returncode == 0 else Path.cwd()))
