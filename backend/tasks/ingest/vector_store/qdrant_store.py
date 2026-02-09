from qdrant_client.models import PointStruct
from backend.infra.db import get_qdrant_client, get_collection_name, create_collection
import uuid


def insert_chunks(chunks):
    client = get_qdrant_client()
    collection_name = get_collection_name()

    if not chunks:
        return

    vector_size = len(chunks[0]["embedding"])
    create_collection(vector_size)

    points = []

    for chunk in chunks:
        text = chunk.get("text") or chunk.get("content") or chunk.get("chunk")

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=chunk["embedding"],
                payload={
                    "text": text,
                    "file_path": chunk.get("file_path", "")
                }
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points
    )
