from types import SimpleNamespace

import backend.infra.db as db


class FakeClient:
    def __init__(self):
        self.created = []
        self.collections = [SimpleNamespace(name="code_embeddings")]

    def get_collections(self):
        return SimpleNamespace(collections=self.collections)

    def create_collection(self, **kwargs):
        self.collections.append(SimpleNamespace(name=kwargs["collection_name"]))

    def create_payload_index(self, **kwargs):
        self.created.append((kwargs["field_name"], kwargs["field_schema"]))


def test_create_collection_ensures_payload_indexes(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(db, "get_qdrant_client", lambda: fake)
    monkeypatch.setattr(db, "get_collection_name", lambda: "code_embeddings")

    db.create_collection(768)

    fields = {name for name, _ in fake.created}
    assert fields == {"repo_url", "file_path", "chunk_type"}
