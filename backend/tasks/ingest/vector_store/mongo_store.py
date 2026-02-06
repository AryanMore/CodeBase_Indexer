from typing import List, Dict
from backend.infra.db import get_collection


def insert_chunks(chunks: List[Dict]) -> None:
    if not chunks:
        return

    collection = get_collection()
    collection.insert_many(chunks)
