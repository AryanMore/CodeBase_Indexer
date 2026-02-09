import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

load_dotenv()

_client = None

def get_qdrant_client():
    global _client

    if _client is None:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", 6333))
        _client = QdrantClient(host=host, port=port)

    return _client


def get_collection_name():
    return os.getenv("QDRANT_COLLECTION_NAME", "code_embeddings")


def create_collection(vector_size: int):
    client = get_qdrant_client()
    collection_name = get_collection_name()

    collections = [c.name for c in client.get_collections().collections]

    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )


def clear_collection():
    client = get_qdrant_client()
    collection_name = get_collection_name()

    client.delete_collection(collection_name=collection_name)
