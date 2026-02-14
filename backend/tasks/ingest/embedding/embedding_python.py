import ast
from pathlib import Path
from typing import List, Dict, Optional


LANGUAGE = "python"
SUPPORTED_EXTENSIONS = {".py"}
implements_uses = True


# -------------------------
# Helpers
# -------------------------

def claim_span(start, end, used_lines):
    for i in range(start, end):
        used_lines.add(i)



def extract_content(lines: List[str], start: int, end: int) -> str:
    return "\n".join(lines[start:end])


def extract_uses(node: ast.AST) -> List[str]:
    uses = set()

    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func

            if isinstance(func, ast.Name):
                uses.add(func.id)

            elif isinstance(func, ast.Attribute):
                uses.add(func.attr)

    return list(uses)


# -------------------------
# Docstring
# -------------------------

def extract_docstring(
    tree: ast.Module,
    lines: List[str],
    used_lines: set
) -> Optional[Dict]:

    if not tree.body:
        return None

    first = tree.body[0]

    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        start = first.lineno - 1
        end = first.end_lineno

        claim_span(start, end, used_lines)

        return {
            "language": LANGUAGE,
            "chunk_type": "python_docstring",
            "content": extract_content(lines, start, end)
        }

    return None


# -------------------------
# Classes
# -------------------------

def extract_classes(
    tree: ast.Module,
    lines: List[str],
    used_lines: set
) -> List[Dict]:

    chunks = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):

            method_nodes = [
                n for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]

            # --- Member Functions First ---
            for method in method_nodes:
                if node.decorator_list:
                    start = min(d.lineno for d in node.decorator_list) - 1
                else:
                    start = node.lineno - 1

                end = method.end_lineno

                claim_span(start, end, used_lines)

                chunks.append({
                    "language": LANGUAGE,
                    "chunk_type": "python_class_function",
                    "content": extract_content(lines, start, end),
                    "identifier": method.name,
                    "class_name": node.name,
                    "uses": extract_uses(method)
                })

            # --- Class Header (Remaining Class-Level Code) ---
            class_start = node.lineno - 1
            class_end = node.end_lineno

            header_lines = []

            for i in range(class_start, class_end):
                if i not in used_lines:
                    header_lines.append(lines[i])
                    used_lines.add(i)

            # Compute header-level uses ONLY (exclude method bodies)
            header_uses = set()

            for child in node.body:
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    header_uses.update(extract_uses(child))

            chunks.append({
                "language": LANGUAGE,
                "chunk_type": "python_class_header",
                "content": "\n".join(header_lines),
                "identifier": node.name,
                "member_functions": [m.name for m in method_nodes],
                "uses": list(header_uses)
            })

    return chunks


# -------------------------
# Top-Level Functions
# -------------------------

def extract_functions(
    tree: ast.Module,
    lines: List[str],
    used_lines: set
) -> List[Dict]:

    chunks = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

            if node.decorator_list:
                start = min(d.lineno for d in node.decorator_list) - 1
            else:
                start = node.lineno - 1

            end = node.end_lineno

            claim_span(start, end, used_lines)

            chunks.append({
                "language": LANGUAGE,
                "chunk_type": "python_function",
                "content": extract_content(lines, start, end),
                "identifier": node.name,
                "uses": extract_uses(node)
            })

    return chunks


# -------------------------
# Imports (Remaining Only)
# -------------------------

def extract_imports(
    tree: ast.Module,
    lines: List[str],
    used_lines: set
) -> Optional[Dict]:

    import_lines = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start = node.lineno - 1
            end = node.end_lineno

            for i in range(start, end):
                if i not in used_lines:
                    import_lines.append(lines[i])
                    used_lines.add(i)

    if not import_lines:
        return None

    return {
        "language": LANGUAGE,
        "chunk_type": "python_import",
        "content": "\n".join(import_lines)
    }


# -------------------------
# Remaining Top-Level Code
# -------------------------

def extract_top_level_code(
    lines: List[str],
    used_lines: set
) -> Optional[Dict]:

    remaining = []

    for i, line in enumerate(lines):
        if i not in used_lines and line.strip():
            remaining.append(line)
            used_lines.add(i)

    if not remaining:
        return None

    return {
        "language": LANGUAGE,
        "chunk_type": "python_top_level_code",
        "content": "\n".join(remaining),
        "uses": []
    }


# -------------------------
# Main Extraction Entry
# -------------------------

def extract_chunks(file_path: Path) -> List[Dict]:

    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    used_lines = set()
    chunks = []

    # 1️⃣ Docstring
    doc = extract_docstring(tree, lines, used_lines)
    if doc:
        chunks.append(doc)

    # 2️⃣ Classes (member functions -> header)
    chunks.extend(extract_classes(tree, lines, used_lines))

    # 3️⃣ Top-Level Functions
    chunks.extend(extract_functions(tree, lines, used_lines))

    # 4️⃣ Imports
    imports = extract_imports(tree, lines, used_lines)
    if imports:
        chunks.append(imports)

    # 5️⃣ Remaining Top-Level Code
    top_level = extract_top_level_code(lines, used_lines)
    if top_level:
        chunks.append(top_level)

    return chunks
