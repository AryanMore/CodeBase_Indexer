from AI_Agent.graph.nodes.intent import intent_node
from AI_Agent.graph.nodes.planner import planner_node
from AI_Agent.schemas.intent import Intent


def _state(query: str):
    return {
        "user_query": query,
        "repo_url": "https://github.com/example/repo",
        "session_id": "s1",
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


def test_intent_node_uses_heuristic_for_explain_without_llm(monkeypatch):
    state = _state("What does this repository do?")

    def fail_chat(*args, **kwargs):
        raise AssertionError("chat should not be called for explain fast-path")

    monkeypatch.setattr("AI_Agent.graph.nodes.intent.chat", fail_chat)

    result = intent_node(state)
    assert result["intent"] == Intent.EXPLAIN


def test_planner_node_uses_static_plan_for_explain_without_llm(monkeypatch):
    state = _state("Explain the API flow")
    state["intent"] = Intent.EXPLAIN

    def fail_chat(*args, **kwargs):
        raise AssertionError("chat should not be called for explain planner fast-path")

    monkeypatch.setattr("AI_Agent.graph.nodes.planner.chat", fail_chat)

    result = planner_node(state)
    assert result["plan"].intent == Intent.EXPLAIN.value
    assert result["plan"].requires_expansion is True
    assert result["plan"].requires_full_file is False
