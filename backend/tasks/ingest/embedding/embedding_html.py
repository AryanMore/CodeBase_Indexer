from pathlib import Path
from typing import List, Dict, Set
from bs4 import BeautifulSoup, Tag


LANGUAGE = "html"
SUPPORTED_EXTENSIONS = {".html"}
implements_uses = False


PRIMARY_TAGS = [
    "section",
    "article",
    "nav",
    "form",
    "header",
    "footer",
]


# -------------------------
# Helpers
# -------------------------

def take_tag(tag: Tag) -> str:
    return str(tag)


def mark_used(tag: Tag, used_nodes: Set[int]):
    used_nodes.add(id(tag))
    for descendant in tag.descendants:
        if isinstance(descendant, Tag):
            used_nodes.add(id(descendant))


# -------------------------
# Main Extraction
# -------------------------

def extract_chunks(file_path: Path) -> List[Dict]:

    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    soup = BeautifulSoup(source, "html.parser")
    used_nodes: Set[int] = set()
    chunks: List[Dict] = []

    # 1️⃣ <main> dominates everything
    main_tag = soup.find("main")
    if main_tag:
        mark_used(main_tag, used_nodes)
        chunks.append({
            "language": LANGUAGE,
            "chunk_type": "html_main_section",
            "content": take_tag(main_tag)
        })
        return chunks

    # 2️⃣ Primary structural tags
    for tag_name in PRIMARY_TAGS:
        for tag in soup.find_all(tag_name):
            if id(tag) in used_nodes:
                continue

            mark_used(tag, used_nodes)

            chunk_type_map = {
                "nav": "html_navigation_block",
                "form": "html_form_block",
                "section": "html_component_block",
                "article": "html_component_block",
                "header": "html_component_block",
                "footer": "html_component_block",
            }

            chunks.append({
                "language": LANGUAGE,
                "chunk_type": chunk_type_map.get(tag.name, "html_component_block"),
                "content": take_tag(tag)
            })

    # 3️⃣ Script blocks
    for tag in soup.find_all("script"):
        if id(tag) in used_nodes:
            continue

        mark_used(tag, used_nodes)

        external_scripts = []
        if tag.has_attr("src"):
            external_scripts.append(tag["src"])

        chunks.append({
            "language": LANGUAGE,
            "chunk_type": "html_script_block",
            "content": take_tag(tag),
            "external_scripts": external_scripts
        })

    # 4️⃣ Style blocks
    for tag in soup.find_all("style"):
        if id(tag) in used_nodes:
            continue

        mark_used(tag, used_nodes)

        chunks.append({
            "language": LANGUAGE,
            "chunk_type": "html_style_block",
            "content": take_tag(tag)
        })

    # 5️⃣ Remaining top-level markup
    remaining = []

    body_iter = soup.body.descendants if soup.body else soup.descendants

    for element in body_iter:
        if isinstance(element, Tag):
            if id(element) in used_nodes:
                continue
            if element.name in ["script", "style"]:
                continue

            text = str(element).strip()
            if text:
                remaining.append(text)
                used_nodes.add(id(element))

    if remaining:
        chunks.append({
            "language": LANGUAGE,
            "chunk_type": "html_top_level_markup",
            "content": "\n".join(remaining)
        })

    return chunks
