import math
from typing import List, Dict

from backend.infra.db import get_collection


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve(query_embedding: List[float], top_k: int = 3) -> List[Dict]:
    collection = get_collection()

    scored = []

    for doc in collection.find({}, {"content": 1, "embedding": 1, "file_path": 1, "chunk_index": 1}):
        score = _cosine_similarity(query_embedding, doc["embedding"])
        scored.append({
            "content": doc["content"],
            "file_path": doc["file_path"],
            "chunk_index": doc["chunk_index"],
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
