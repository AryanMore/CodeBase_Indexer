from fastapi.testclient import TestClient

import backend.main as main


client = TestClient(main.app)


def test_agent_query_endpoint(monkeypatch):
    def fake_run_agent(user_query: str, repo_url: str, session_id=None):
        return {
            "session_id": session_id or "sess-1",
            "explanation": f"agent answer for {user_query} @ {repo_url}",
        }

    monkeypatch.setattr(main, "run_agent", fake_run_agent)

    response = client.post(
        "/agent/query",
        json={
            "repo_url": "https://github.com/example/repo",
            "question": "what does this do?",
            "session_id": "abc123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "abc123"
    assert "agent answer" in payload["answer"]
