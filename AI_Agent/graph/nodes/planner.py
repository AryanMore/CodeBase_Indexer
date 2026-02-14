from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, extract_json, render_prompt
from AI_Agent.schemas.intent import Intent
from AI_Agent.schemas.plan import Plan


def planner_node(state: AgentState) -> AgentState:
    # Fast-path for common informational queries: avoid an extra LLM call
    # while preserving context quality (retrieval + expansion still enabled).
    if state["intent"] in {Intent.EXPLAIN, Intent.LOCATE, Intent.ANALYZE}:
        state["plan"] = Plan(
            intent=state["intent"].value,
            steps=["Retrieve relevant chunks", "Answer with grounded context"],
            requires_expansion=True,
            requires_full_file=False,
            target_files=None,
        )
        return state

    prompt = render_prompt(
        "AI_Agent/prompts/planner.txt",
        {
            "intent": state["intent"].value,
            "user_query": state["user_query"],
        },
    )
    response = chat(prompt)

    try:
        plan_data = extract_json(response)
        state["plan"] = Plan(**plan_data)
    except Exception:
        state["plan"] = Plan(
            intent=state["intent"].value,
            steps=["Retrieve relevant chunks", "Answer with grounded context"],
            requires_expansion=True,
            requires_full_file=False,
            target_files=None,
        )

    return state
