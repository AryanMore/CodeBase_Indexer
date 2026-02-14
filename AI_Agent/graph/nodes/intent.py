from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, render_prompt


def intent_node(state: AgentState) -> AgentState:
    prompt = render_prompt(
        "AI_Agent/prompts/intent.txt",
        {"user_query": state["user_query"]},
    )
    response = chat(prompt, max_tokens=20).strip()
    from AI_Agent.schemas.intent import Intent

    try:
        state["intent"] = Intent(response)
    except Exception:
        state["intent"] = Intent.EXPLAIN
    return state
