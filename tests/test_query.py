from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_query_repo():
    response = client.post(
        "/query",
        json={"question": "What does this repository do?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0
