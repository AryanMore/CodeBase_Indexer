from pathlib import Path
from typing import List, Dict


def blind_chunk(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0

    return chunks


def extract_chunks(file_path: Path) -> List[Dict]:

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    raw_chunks = blind_chunk(content)

    structured = []

    for chunk in raw_chunks:
        structured.append({
            "language": "blind",
            "chunk_type": "blind_chunk",
            "content": chunk
        })

    return structured
