from pathlib import Path
from typing import List, Set

from bs4 import BeautifulSoup, Tag

from backend.config import CHUNK_SIZE
from backend.tasks.ingest.embedding.embedding_blind import blind_chunk


PRIMARY_TAGS = [
    "main",
    "section",
    "article",
    "nav",
    "form",
    "header",
    "footer",
]


def extract_html_chunks(file_path: Path) -> List[str]:
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    soup = BeautifulSoup(source, "html.parser")
    used_nodes: Set[int] = set()
    chunks: List[str] = []

    def mark_used(tag: Tag):
        for descendant in tag.descendants:
            if isinstance(descendant, Tag):
                used_nodes.add(id(descendant))
        used_nodes.add(id(tag))

    def take_tag(tag: Tag):
        html = str(tag)
        mark_used(tag)

        if len(html) > CHUNK_SIZE * 1.5:
            return blind_chunk(html)
        return [html]

    # 1️⃣ <main> dominates everything
    main_tag = soup.find("main")
    if main_tag:
        chunks.extend(take_tag(main_tag))
        return chunks

    # 2️⃣ Other primary structural tags (top-level only)
    for tag_name in PRIMARY_TAGS:
        for tag in soup.find_all(tag_name, recursive=True):
            if id(tag) in used_nodes:
                continue

            # Skip nested structural tags
            parent = tag.parent
            while parent:
                if isinstance(parent, Tag) and parent.name in PRIMARY_TAGS:
                    break
                parent = parent.parent
            else:
                chunks.extend(take_tag(tag))

    # 3️⃣ Remaining visible HTML
    remaining = []

    for element in soup.body.descendants if soup.body else soup.descendants:
        if isinstance(element, Tag):
            if id(element) in used_nodes:
                continue
            if element.name in ["script", "style"]:
                continue
            text = str(element).strip()
            if text:
                remaining.append(text)

    if remaining:
        block = "\n".join(remaining)
        if len(block) > CHUNK_SIZE * 1.5:
            chunks.extend(blind_chunk(block))
        else:
            chunks.append(block)

    if not chunks:
        return blind_chunk(source)

    return chunks
