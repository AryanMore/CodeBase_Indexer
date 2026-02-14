import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams
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


def _ensure_payload_indexes(client: QdrantClient, collection_name: str):
    # Filter-heavy query paths (/rag/retrieve and /rag/expand) rely on these fields.
    # Keeping payload indexes in place avoids expensive full scans.
    indexed_fields = {
        "repo_url": PayloadSchemaType.KEYWORD,
        "file_path": PayloadSchemaType.KEYWORD,
        "chunk_type": PayloadSchemaType.KEYWORD,
    }

    for field_name, schema in indexed_fields.items():
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema,
                wait=True,
            )
        except Exception:
            # Index may already exist, or backend may return a non-fatal conflict.
            # Query path remains functional either way.
            pass


def create_collection(vector_size: int):
    client = get_qdrant_client()
    collection_name = get_collection_name()

    collections = [c.name for c in client.get_collections().collections]

    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    _ensure_payload_indexes(client, collection_name)


def clear_collection():
    client = get_qdrant_client()
    collection_name = get_collection_name()

    client.delete_collection(collection_name=collection_name)


class _QdrantCollectionAdapter:
    def __init__(self, client, collection_name):
        self.client = client
        self.collection_name = collection_name

    def count_documents(self, _filter=None):
        result = self.client.count(collection_name=self.collection_name, exact=True)
        return result.count


def get_collection():
    """Backward-compatible adapter for legacy tests expecting a Mongo-style collection."""
    return _QdrantCollectionAdapter(get_qdrant_client(), get_collection_name())
