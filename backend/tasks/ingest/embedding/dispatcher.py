from pathlib import Path
from typing import List, Dict

from backend.infra.llm import embed_text
from backend.tasks.ingest.embedding.embedding_blind import blind_chunk
from backend.tasks.ingest.embedding.embedding_python import extract_python_chunks
from backend.tasks.ingest.embedding.embedding_html import extract_html_chunks


def embed_file(file_path: Path) -> List[Dict]:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    if file_path.suffix.lower() == ".py":
        chunks = extract_python_chunks(file_path)
    elif file_path.suffix.lower() == ".html":
        chunks=extract_html_chunks(file_path)
    else:
        chunks = blind_chunk(content)

    embedded_chunks = []

    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk)
        embedded_chunks.append({
            "content": chunk,
            "embedding": embedding,
            "file_path": str(file_path),
            "chunk_index": i
        })

    return embedded_chunks
