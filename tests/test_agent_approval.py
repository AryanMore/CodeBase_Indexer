from AI_Agent.graph.graph import OrchestratorGraph
from AI_Agent.memory.store import memory
from AI_Agent.schemas.diff import DiffBundle, FileDiff


def test_approval_query_applies_pending_bundle(monkeypatch):
    session_id = "s-approval"
    memory.set_pending_diff(
        session_id,
        DiffBundle(
            bundle_id="bundle-1",
            goal="change file",
            files=[FileDiff(file_path="a.py", diff="diff --git a/a.py b/a.py")],
            explanation="proposal",
        ),
    )

    called = {"applied": False}

    def fake_apply(state):
        called["applied"] = True
        state["explanation"] = "Changes applied, committed, and pushed to origin/work"
        return state

    monkeypatch.setattr("AI_Agent.graph.graph.apply_node", fake_apply)

    graph = OrchestratorGraph()
    state = {
        "user_query": "APPROVE",
        "repo_url": "https://github.com/example/repo",
        "session_id": session_id,
        "chat_history": [],
        "intent": None,
        "plan": None,
        "retrieved_chunks": [],
        "expanded_chunks": [],
        "file_chunks": [],
        "explanation": None,
        "proposed_diff_id": None,
        "approved": False,
    }

    result = graph.invoke(state)

    assert called["applied"] is True
    assert result["approved"] is True
    assert result["proposed_diff_id"] == "bundle-1"
    assert "pushed" in result["explanation"].lower()
    assert memory.get_pending_diff(session_id) is None
