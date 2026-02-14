from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, extract_json, render_prompt
from AI_Agent.schemas.plan import Plan


def planner_node(state: AgentState) -> AgentState:
    """
    Build an internal execution plan.

    If the LLM returns invalid JSON, we attempt a single structured repair pass
    before falling back to a safe default plan.
    """
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
        return state
    except Exception:
        # One repair attempt: ask the model to fix the JSON only.
        repair_prompt = (
            "Your previous response did not match the required strict JSON schema.\n\n"
            "Original instructions:\n"
            f"{prompt}\n\n"
            "Your previous response:\n"
            f"{response}\n\n"
            "Respond again with ONLY valid JSON that matches the specified schema, "
            "with no extra commentary or surrounding text."
        )
        repaired = chat(repair_prompt)
        try:
            plan_data = extract_json(repaired)
            state["plan"] = Plan(**plan_data)
            return state
        except Exception:
            # Final defensive fallback plan, fully grounded and non-destructive.
            state["plan"] = Plan(
                intent=state["intent"].value,
                steps=["Retrieve relevant chunks", "Answer with grounded context"],
                requires_expansion=True,
                requires_full_file=False,
                target_files=None,
            )
            return state
