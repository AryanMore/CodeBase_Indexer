from fastapi.testclient import TestClient
from backend.main import app
from backend.infra.db import get_collection

client = TestClient(app)


def test_ingest_repo():
    response = client.post(
        "/ingest",
        json={"repo_url": "https://github.com/khushb-glide/FastAPiMongoCRUD"}
    )

    assert response.status_code == 200

    collection = get_collection()
    count = collection.count_documents({})
    assert count > 0
