from typing import List

from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


def blind_chunk(text: str) -> List[str]:
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
        if start < 0:
            start = 0

    return chunks
