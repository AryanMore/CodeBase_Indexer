from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, extract_json, render_prompt
from AI_Agent.schemas.plan import Plan


def planner_node(state: AgentState) -> AgentState:
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
