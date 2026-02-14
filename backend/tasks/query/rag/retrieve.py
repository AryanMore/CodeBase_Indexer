from backend.infra.db import get_qdrant_client, get_collection_name


def retrieve(query_embedding, top_k=5):
    client = get_qdrant_client()
    collection_name = get_collection_name()

    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        limit=top_k
    )

    chunks = []

    for point in results.points:
        chunks.append({
            "text": point.payload.get("content", ""),
            "file_path": point.payload.get("file_path", "")
        })

    return chunks
