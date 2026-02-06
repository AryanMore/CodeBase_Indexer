import ast
from pathlib import Path
from typing import List

from backend.config import CHUNK_SIZE
from backend.tasks.ingest.embedding.embedding_blind import blind_chunk


def extract_python_chunks(file_path: Path) -> List[str]:
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return blind_chunk(source)

    lines = source.splitlines()
    used_lines = set()
    chunks: List[str] = []

    def take_block(start: int, end: int):
        for i in range(start, end):
            used_lines.add(i)
        block = "\n".join(lines[start:end])
        if len(block) > CHUNK_SIZE * 1.5:
            return blind_chunk(block)
        return [block]

    # 1️⃣ Module docstring
    docstring = ast.get_docstring(tree)
    if docstring and tree.body:
        node = tree.body[0]
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            start = node.lineno - 1
            end = node.end_lineno
            chunks.extend(take_block(start, end))

    # 2️⃣ Imports (grouped)
    import_nodes = [
        n for n in tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    if import_nodes:
        start = import_nodes[0].lineno - 1
        end = import_nodes[-1].end_lineno
        chunks.extend(take_block(start, end))

    # 3️⃣ Classes
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            chunks.extend(
                take_block(node.lineno - 1, node.end_lineno)
            )

    # 4️⃣ Top-level functions (not in classes)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.extend(
                take_block(node.lineno - 1, node.end_lineno)
            )

    # 5️⃣ Remaining top-level code
    remaining = []
    for i, line in enumerate(lines):
        if i not in used_lines and line.strip():
            remaining.append(line)

    if remaining:
        block = "\n".join(remaining)
        if len(block) > CHUNK_SIZE * 1.5:
            chunks.extend(blind_chunk(block))
        else:
            chunks.append(block)

    if not chunks:
        return blind_chunk(source)

    return chunks
