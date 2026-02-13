from qdrant_client.models import PointStruct
from backend.infra.db import get_qdrant_client, get_collection_name, create_collection
import uuid


def insert_chunks(chunks):

    if not chunks:
        return

    client = get_qdrant_client()
    collection_name = get_collection_name()

    vector_size = len(chunks[0]["embedding"])
    create_collection(vector_size)

    points = []

    for chunk in chunks:

        payload = {
            "content": chunk.get("content"),
            "language": chunk.get("language"),
            "chunk_type": chunk.get("chunk_type"),
            "file_path": chunk.get("file_path"),
            "chunk_number": chunk.get("chunk_number"),
        }

        # Optional metadata
        if "identifier" in chunk:
            payload["identifier"] = chunk["identifier"]

        if "uses" in chunk:
            payload["uses"] = chunk["uses"]

        if "class_name" in chunk:
            payload["class_name"] = chunk["class_name"]

        if "member_functions" in chunk:
            payload["member_functions"] = chunk["member_functions"]

        if "repo_url" in chunk:
            payload["repo_url"] = chunk["repo_url"]

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=chunk["embedding"],
                payload=payload
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points
    )
