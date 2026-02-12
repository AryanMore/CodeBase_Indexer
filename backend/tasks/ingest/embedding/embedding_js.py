from pathlib import Path
from typing import List, Dict

from tree_sitter import Parser, Language
from tree_sitter_javascript import language as javascript_capsule

JS_LANGUAGE = Language(javascript_capsule())

parser = Parser()
parser.language = JS_LANGUAGE





LANGUAGE = "javascript"
SUPPORTED_EXTENSIONS = {".js"}
implements_uses = True


# -------------------------
# Helpers
# -------------------------

def get_node_text(source_bytes: bytes, node):
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")


def extract_identifier_from_function(node, source_bytes):
    for child in node.children:
        if child.type == "identifier":
            return get_node_text(source_bytes, child)
    return None


def extract_uses(node, source_bytes):
    uses = set()

    stack = [node]

    while stack:
        current = stack.pop()

        if current.type == "call_expression":
            func_node = current.child_by_field_name("function")
            if func_node:
                if func_node.type == "identifier":
                    uses.add(get_node_text(source_bytes, func_node))
                elif func_node.type == "member_expression":
                    prop = func_node.child_by_field_name("property")
                    if prop and prop.type == "property_identifier":
                        uses.add(get_node_text(source_bytes, prop))

        stack.extend(current.children)

    return list(uses)


# -------------------------
# Main Extraction
# -------------------------

def extract_chunks(file_path: Path) -> List[Dict]:

    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    source_bytes = source.encode("utf-8")
    tree = parser.parse(source_bytes)
    root = tree.root_node

    chunks = []
    claimed_ranges = []

    def claim(node):
        claimed_ranges.append((node.start_byte, node.end_byte))

    def is_claimed(node):
        for start, end in claimed_ranges:
            if node.start_byte >= start and node.end_byte <= end:
                return True
        return False

    # 1️⃣ Import statements
    import_nodes = [n for n in root.children if n.type == "import_statement"]
    if import_nodes:
        start = import_nodes[0].start_byte
        end = import_nodes[-1].end_byte
        content = source_bytes[start:end].decode("utf-8", errors="ignore")
        chunks.append({
            "language": LANGUAGE,
            "chunk_type": "javascript_import",
            "content": content
        })
        claimed_ranges.append((start, end))

    # 2️⃣ Class Declarations
    for node in root.children:
        if node.type == "class_declaration" and not is_claimed(node):

            class_name = None
            for child in node.children:
                if child.type == "identifier":
                    class_name = get_node_text(source_bytes, child)
                    break

            class_body_node = None
            for child in node.children:
                if child.type == "class_body":
                    class_body_node = child
                    break

            member_functions = []
            header_uses = set()

            if class_body_node:

                for element in class_body_node.children:

                    # --- Member Functions ---
                    if element.type == "method_definition":

                        name_node = element.child_by_field_name("name")
                        if name_node:
                            method_name = get_node_text(source_bytes, name_node)
                            member_functions.append(method_name)

                            chunks.append({
                                "language": LANGUAGE,
                                "chunk_type": "javascript_class_function",
                                "content": get_node_text(source_bytes, element),
                                "identifier": method_name,
                                "class_name": class_name,
                                "uses": extract_uses(element, source_bytes)
                            })

                            claim(element)

                    # --- Header-Level Elements (static fields, etc.) ---
                    else:
                        header_uses.update(extract_uses(element, source_bytes))

            # Class header
            header_content = get_node_text(source_bytes, node)

            chunks.append({
                "language": LANGUAGE,
                "chunk_type": "javascript_class_header",
                "content": header_content,
                "identifier": class_name,
                "member_functions": member_functions,
                "uses": list(header_uses)
            })

            claim(node)


    # 3️⃣ Function Declarations
    for node in root.children:
        if node.type == "function_declaration" and not is_claimed(node):

            identifier = extract_identifier_from_function(node, source_bytes)

            chunks.append({
                "language": LANGUAGE,
                "chunk_type": "javascript_function",
                "content": get_node_text(source_bytes, node),
                "identifier": identifier,
                "uses": extract_uses(node, source_bytes)
            })

            claim(node)

    # 4️⃣ Remaining Top-Level Code
    remaining = []
    for node in root.children:
        if not is_claimed(node):
            remaining.append(get_node_text(source_bytes, node))
            claim(node)

    if remaining:
        chunks.append({
            "language": LANGUAGE,
            "chunk_type": "javascript_top_level_code",
            "content": "\n".join(remaining),
            "uses": []
        })

    return chunks
