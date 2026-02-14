from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, render_prompt
from AI_Agent.schemas.intent import Intent


MODIFY_HINTS = {
    "change",
    "modify",
    "edit",
    "update",
    "rewrite",
    "implement",
    "add",
    "remove",
    "refactor",
    "fix",
    "bug",
    "optimize",
}


def _heuristic_intent(user_query: str):
    text = user_query.lower().strip()
    if not text:
        return Intent.EXPLAIN

    if any(hint in text for hint in MODIFY_HINTS):
        if "refactor" in text:
            return Intent.REFACTOR
        if "bug" in text or "fix" in text:
            return Intent.DEBUG
        return Intent.MODIFY

    # Most user queries are informational Q&A; shortcut to avoid an LLM call.
    return Intent.EXPLAIN


def intent_node(state: AgentState) -> AgentState:
    heuristic = _heuristic_intent(state["user_query"])
    if heuristic in {Intent.EXPLAIN, Intent.MODIFY, Intent.REFACTOR, Intent.DEBUG}:
        state["intent"] = heuristic
        return state

    prompt = render_prompt(
        "AI_Agent/prompts/intent.txt",
        {"user_query": state["user_query"]},
    )
    response = chat(prompt, max_tokens=20).strip()

    try:
        state["intent"] = Intent(response)
    except Exception:
        state["intent"] = Intent.EXPLAIN
    return state
