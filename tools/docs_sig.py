"""What a caller of a source file can use, per language: the signatures `python tools/docs.py sig` prints, one
member's lines for `sig Name:member`, and the test names `close` writes into a record.

Each language is an adapter: signatures(text, include_private) gives (line, depth, signature, doc summary)
for each declaration a caller can reach, and member_ranges(text, member) gives each declaration of member as
(first, last) lines, its doc comment and decorators included. Java and TypeScript/JavaScript are read by
counting braces outside strings and comments; Python by its own parser. Standard library only.
"""

import ast
import re
from pathlib import Path

SUMMARY_LIMIT = 200  # characters of a doc comment's first sentence


def first_sentence(text):
    """A doc comment's first sentence, cut at SUMMARY_LIMIT characters; None for no text."""
    text = " ".join((text or "").split())
    if not text:
        return None
    sentence = re.match(r"(.+?\.)(?:\s|$)", text)
    text = sentence.group(1) if sentence else text
    return text if len(text) <= SUMMARY_LIMIT else text[:SUMMARY_LIMIT - 1] + "…"


def doc_comment_summary(lines):
    """A /** ... */ comment's first sentence, its tags reduced to their text (Javadoc and JSDoc alike)."""
    parts = []
    for line in lines:
        line = re.sub(r"^/\*\*|\*/$", "", line.strip()).strip()
        line = line[1:].strip() if line.startswith("*") else line
        if line.startswith("@"):
            break
        parts.append(line)
    text = " ".join(part for part in parts if part)
    text = re.sub(r"\{@(?:link|linkplain|code|value)\s+([^}]*)\}", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return first_sentence(text)


def brace_range(lines, start, strip):
    """(start, last) from a declaration's first line to the brace closing its body, or to its ';' if it has none."""
    depth, opened, last = 0, False, start
    for n in range(start, len(lines) + 1):
        code = strip(lines[n - 1])
        for char in code:
            if char == "{":
                depth, opened = depth + 1, True
            elif char == "}":
                depth -= 1
        last = n
        if (opened and depth <= 0) or (not opened and ";" in code):
            break
    return last


def comment_start(lines, start):
    """The first line of the doc comment and annotations or decorators above a declaration's line."""
    first = start
    while first > 1 and re.match(r"\s*(@|\*|/\*\*|\*/)", lines[first - 2]):
        first -= 1
    return first


# --- Java --------------------------------------------------------------------------------------

JAVA_TYPE = re.compile(r"\b(class|interface|enum|record)\s+\w+")
JAVA_LITERAL = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
JAVA_ANNOTATION = re.compile(r"^@\w+(?:\.\w+)*(?:\([^)]*\))?\s*")


def java_code(line):
    return re.sub(r"//.*", "", JAVA_LITERAL.sub('""', line))


def depth_of(stack):
    return sum(1 for entry in stack if entry[0] in ("type", "enum"))


def hidden(stack):
    """Inside a private type, whose members no caller outside its class can reach."""
    return any(entry[2] for entry in stack)


def java_signatures(text, include_private=False):
    """Each type, constructor, method, field and enum constant declared at the top level or directly in a type's
    body and not private (with include_private, private ones too). Bodies are skipped by counting braces
    outside strings and comments."""
    found = []
    stack = []  # one entry per open brace: [kind, enum constants still to come, a private type's body]
    summary, javadoc, in_javadoc, in_comment = None, [], False, False
    pending, start, pending_summary = None, 0, None
    for n, raw in enumerate(text.split("\n"), 1):
        line = raw.strip()
        if in_javadoc:
            javadoc.append(line)
            if "*/" in line:
                in_javadoc, summary = False, doc_comment_summary(javadoc)
            continue
        if in_comment:
            in_comment = "*/" not in line
            continue
        if line.startswith("/**"):
            javadoc = [line]
            if "*/" in line[3:]:
                summary = doc_comment_summary(javadoc)
            else:
                in_javadoc = True
            continue
        if line.startswith("/*"):
            in_comment = "*/" not in line[2:]
            continue
        code = java_code(line).strip()
        if not code:
            continue
        in_body = not stack or stack[-1][0] in ("type", "enum")
        if pending is None and in_body:
            while JAVA_ANNOTATION.match(code):
                code = JAVA_ANNOTATION.sub("", code, count=1)
            if not code or code.startswith(("package ", "import ")):
                continue
            if stack and stack[-1][0] == "enum" and stack[-1][1] and code[0] != "}":
                # Enum constants, up to the ';' that ends them, by name alone.
                ends = ";" in code
                constants = re.sub(r"\([^()]*\)", "", code.split(";")[0])
                names = ", ".join(re.findall(r"[A-Za-z_]\w*", constants))
                if names and (include_private or not hidden(stack)):
                    found.append((n, depth_of(stack), names, summary))
                summary = None
                stack[-1][1] = not ends
                continue
            if not code.startswith(("}", "{", "static {")) and code != "static":
                pending, start, pending_summary, summary = "", n, summary, None
        if pending is not None:
            pending = (pending + " " + code).strip()
            stops = [i for i in (pending.find("{"), pending.find(";")) if i >= 0]
            if not stops:
                continue
            stop = min(stops)
            head = pending[:stop]
            field = "=" in head.split("(")[0] or ("=" in head and "(" not in head)
            signature = head.split("=")[0] if field else head
            signature = re.sub(r"\s+", " ", signature).strip()
            private = bool(re.search(r"\bprivate\b", signature.split("(")[0]))
            if signature and (include_private or not private and not hidden(stack)):
                found.append((start, depth_of(stack), signature, pending_summary))
            opens_type = pending[stop] == "{" and not field and JAVA_TYPE.search(head)
            kind = ("enum" if opens_type.group(1) == "enum" else "type") if opens_type else "other"
            # Braces on this line: the declaration's own, then any others after it.
            rest = code[code.find("{"):] if pending[stop] == "{" and "{" in code else ""
            pending = None
            for i, char in enumerate(rest):
                if char == "{":
                    stack.append([kind, kind == "enum", private] if i == 0 else ["other", False, False])
                elif char == "}" and stack:
                    stack.pop()
            continue
        for char in code:
            if char == "{":
                stack.append(["other", False, False])
            elif char == "}" and stack:
                stack.pop()
    return found


def member_name(signature):
    """'public static long add(Level level, …)' -> 'add'; a field's or type's own name likewise."""
    head = signature.split("(")[0] if "(" in signature else signature
    declared = re.search(r"\b(?:class|interface|enum|record|type|namespace)\s+([\w$]+)", head)
    if declared:
        return declared.group(1)
    while re.search(r"<[^<>]*>", head):
        head = re.sub(r"<[^<>]*>", "", head)  # 'List<Recipe> recipes' names the method, not List
    head = head.split(":")[0] if ":" in head and "(" not in signature else head
    words = re.findall(r"[#A-Za-z_$][\w$]*", head)
    return words[-1].lstrip("#") if words else ""


def java_member_ranges(text, member):
    """Each declaration of member (method, constructor, field or type) as (first, last) lines, its javadoc and
    annotations included, its body to the brace that closes it. Private members count: this is read before
    an edit, not by a caller."""
    lines = text.split("\n")
    ranges = []
    for start, _, signature, _ in java_signatures(text, include_private=True):
        # Enum constants share one signature, 'ONE, TWO'.
        names = signature.split(", ") if "(" not in signature and "," in signature else [member_name(signature)]
        if member in names:
            ranges.append((comment_start(lines, start), brace_range(lines, start, java_code)))
    return ranges


# --- TypeScript and JavaScript ------------------------------------------------------------------

TS_LITERAL = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`')
TS_TOP = re.compile(r"^(?:export\s+(?:default\s+)?)?(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?"
                    r"(function\*?|class|interface|type|enum|const|let|var|namespace)\b")
TS_MEMBER = re.compile(r"^(?:(?:public|private|protected|static|readonly|abstract|override|async|declare|get|set)\s+)*"
                       r"\*?(#?[A-Za-z_$][\w$]*)\s*[?!]?\s*(?:<[^>]*>)?\s*[(:=;]")
TS_PRIVATE = re.compile(r"^(?:\w+\s+)*?(private|protected)\b|^(?:\w+\s+)*#")


def ts_code(line):
    return re.sub(r"//.*", "", TS_LITERAL.sub('""', line))


def ts_signature(head):
    """A declaration cut to what a caller needs: no body, no initial value beyond an arrow function's header."""
    head = re.sub(r"\s+", " ", head).strip()
    if re.match(r"(?:export\s+(?:default\s+)?)?(?:declare\s+)?(?:const|let|var)\b", head) or "=" in head.split("(")[0]:
        if "=>" in head:
            return head[:head.index("=>") + 2].strip()
        if re.match(r"(?:export\s+)?type\b", head):
            return head.rstrip("{").strip()
        return head.split("=")[0].strip()
    return head.rstrip("{").strip()


def ts_signatures(text, include_private=False):
    """Each top-level declaration (exported ones only, unless include_private) and each member of a class,
    interface or enum body (not private or protected, unless include_private), with its JSDoc's first sentence."""
    found = []
    stack = []  # one entry per open brace: [kind, a hidden body]
    summary, jsdoc, in_jsdoc, in_comment = None, [], False, False
    pending, start, pending_summary, pending_hidden = None, 0, None, False
    for n, raw in enumerate(text.split("\n"), 1):
        line = raw.strip()
        if in_jsdoc:
            jsdoc.append(line)
            if "*/" in line:
                in_jsdoc, summary = False, doc_comment_summary(jsdoc)
            continue
        if in_comment:
            in_comment = "*/" not in line
            continue
        if line.startswith("/**"):
            jsdoc = [line]
            if "*/" in line[3:]:
                summary = doc_comment_summary(jsdoc)
            else:
                in_jsdoc = True
            continue
        if line.startswith("/*"):
            in_comment = "*/" not in line[2:]
            continue
        code = ts_code(line).strip()
        if not code or code.startswith("@"):
            continue
        top = not stack
        in_type = bool(stack) and stack[-1][0] == "type"
        if pending is None and (top or in_type) and not code.startswith(("}", "import ", "export {", "export *")):
            if top and TS_TOP.match(code):
                exported = code.startswith("export")
                pending, start, pending_summary, pending_hidden = "", n, summary, not exported
            elif in_type and (TS_MEMBER.match(code) or code.startswith("constructor")):
                private = bool(TS_PRIVATE.match(code)) or any(entry[1] for entry in stack)
                pending, start, pending_summary, pending_hidden = "", n, summary, private
            summary = None
        if pending is not None:
            pending = (pending + " " + code).strip()
            stops = [i for i in (pending.find("{"), pending.find(";"), pending.find("=>")) if i >= 0]
            simple = in_type and not stops and not pending.rstrip().endswith((",", "(", "|", "&", ":"))
            if not stops and not simple and n - start < 6:
                continue
            stop = min(stops) if stops else len(pending)
            head = pending[:stop + 2] if stops and pending[stop:stop + 2] == "=>" else pending[:stop]
            signature = ts_signature(head).rstrip(",;")
            if signature and (include_private or not pending_hidden):
                found.append((start, len([e for e in stack if e[0] == "type"]) + 1, signature, pending_summary))
            opens_type = stops and pending[stop] == "{" and re.search(r"\b(class|interface|enum)\s+[\w$]+", head) \
                and "=" not in head.split("{")[0].split("(")[0]
            kind = "type" if opens_type else "other"
            hide = pending_hidden
            pending = None
            first = True
            for char in code:
                if char == "{":
                    stack.append([kind if first else "other", hide])
                    first = False
                elif char == "}" and stack:
                    stack.pop()
            continue
        for char in code:
            if char == "{":
                stack.append(["other", False])
            elif char == "}" and stack:
                stack.pop()
    return found


def ts_member_ranges(text, member):
    lines = text.split("\n")
    return [(comment_start(lines, start), brace_range(lines, start, ts_code))
            for start, _, signature, _ in ts_signatures(text, include_private=True)
            if member_name(signature.split("=>")[0]) == member or ts_declared_name(signature) == member]


def ts_declared_name(signature):
    match = re.search(r"\b(?:function\*?|class|interface|type|enum|const|let|var|namespace)\s+([\w$]+)", signature)
    if match:
        return match.group(1)
    match = TS_MEMBER.match(signature)
    return match.group(1).lstrip("#") if match else ("constructor" if signature.startswith("constructor") else None)


# --- Python ------------------------------------------------------------------------------------


def py_private(name):
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


def py_header(node):
    if isinstance(node, ast.ClassDef):
        bases = ", ".join(ast.unparse(base) for base in node.bases + node.keywords)
        return f"class {node.name}" + (f"({bases})" if bases else "")
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    decorators = [ast.unparse(d) for d in node.decorator_list if ast.unparse(d) in ("staticmethod", "classmethod", "property")]
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return "".join(f"@{d} " for d in decorators) + f"{prefix} {node.name}({ast.unparse(node.args)}){returns}"


def py_assigned(node):
    """(names, signature) for an assignment worth listing, or ([], None)."""
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id], f"{node.target.id}: {ast.unparse(node.annotation)}"
    if isinstance(node, ast.Assign):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if names:
            value = ast.unparse(node.value)
            shown = value if len(value) <= 60 else "…"
            return names, f"{' = '.join(names)} = {shown}"
    return [], None


def py_signatures(text, include_private=False):
    """Classes, functions and methods with their docstring's first sentence; module constants (UPPER_CASE or
    annotated) and class attributes. A leading underscore is private; dunder methods are not."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    found = []

    def visit(body, depth, in_hidden, in_class):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                private = py_private(node.name) or in_hidden
                if include_private or not private:
                    found.append((node.lineno, depth, py_header(node), first_sentence(ast.get_docstring(node))))
                if isinstance(node, ast.ClassDef):
                    visit(node.body, depth + 1, private, True)
            else:
                names, signature = py_assigned(node)
                if not names:
                    continue
                listed = in_class or isinstance(node, ast.AnnAssign) or all(name.isupper() for name in names)
                private = any(py_private(name) for name in names) or in_hidden
                if listed and (include_private or not private):
                    found.append((node.lineno, depth, signature, None))

    visit(tree.body, 1, False, False)
    return found


def py_member_ranges(text, member):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    ranges = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == member:
            first = min([node.lineno] + [d.lineno for d in node.decorator_list])
            ranges.append((first, node.end_lineno))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and member in py_assigned(node)[0]:
            ranges.append((node.lineno, node.end_lineno))
    return sorted(ranges)


# --- adapters ----------------------------------------------------------------------------------

JAVA = (java_signatures, java_member_ranges)
TYPESCRIPT = (ts_signatures, ts_member_ranges)
PYTHON = (py_signatures, py_member_ranges)
ADAPTERS = {".java": JAVA, ".py": PYTHON, ".ts": TYPESCRIPT, ".tsx": TYPESCRIPT, ".mts": TYPESCRIPT,
            ".cts": TYPESCRIPT, ".js": TYPESCRIPT, ".jsx": TYPESCRIPT, ".mjs": TYPESCRIPT, ".cjs": TYPESCRIPT}


def signatures(path, text, include_private=False):
    return ADAPTERS[Path(path).suffix][0](text, include_private)


def member_ranges(path, text, member):
    return ADAPTERS[Path(path).suffix][1](text, member)


def find_sources(sources, name):
    """The sources a name means: a file's stem ('SearchIndex'), a path's tail ('search/SearchIndex'), either
    with its extension."""
    tail = name.replace("\\", "/").strip("/")
    found = []
    for source in sources:
        path = "/" + source
        bare = path[:-len(Path(source).suffix)]
        if path.endswith("/" + tail) or bare.endswith("/" + tail):
            found.append(source)
    return sorted(found)


# --- tests -------------------------------------------------------------------------------------

TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|gametest)/|[._-](test|spec)\.\w+$|(^|/)test_[^/]+\.py$"
                       r"|_test\.py$|Tests?\.java$")


def is_test(path):
    return bool(TEST_PATH.search(path.replace("\\", "/")))


def test_words(name):
    """'aBlockNeverSplits' or 'a_block_never_splits' as 'a block never splits'."""
    name = re.sub(r"^test_?", "", name)
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", name).replace("_", " ").lower().strip()


def added_tests(path, diff):
    """The tests a diff of a test file adds, as words: Java's annotated test methods, Python's test_ functions,
    and the names given to it() and test() in TypeScript and JavaScript."""
    suffix = Path(path).suffix
    names = []
    if suffix == ".java":
        annotated = False
        for line in diff.splitlines():
            if re.match(r"^\+\s*@\w*Test\b", line):
                annotated = True
                continue
            method = re.match(r"^\+.*\bvoid (\w+)\(", line)
            if annotated and method:
                names.append(test_words(method.group(1)))
            if line.startswith("+") and not line.strip("+ \t").startswith("@"):
                annotated = False
    elif suffix == ".py":
        names = [test_words(m) for m in re.findall(r"^\+\s*(?:async\s+)?def (test\w*)\(", diff, re.MULTILINE)]
    elif suffix in ADAPTERS:
        names = [m[1] for m in re.findall(r"^\+\s*(?:it|test)(?:\.\w+)?\(\s*([\"'`])(.+?)\1", diff, re.MULTILINE)]
    return names
