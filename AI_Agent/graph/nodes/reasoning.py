from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, render_prompt
from AI_Agent.memory.store import memory


def reasoning_node(state: AgentState) -> AgentState:
    approved_chunks = state["retrieved_chunks"] + state["expanded_chunks"] + state["file_chunks"]

    context = "\n\n".join(
        f"[{c.file_path}:{c.start_line}-{c.end_line}]\n{c.content}" for c in approved_chunks
    )

    prompt = render_prompt(
        "AI_Agent/prompts/reasoning.txt",
        {
            "context": context,
            "user_query": state["user_query"],
        },
    )

    response = chat(prompt)
    state["explanation"] = response

    if state.get("session_id"):
        memory.add_turn(state["session_id"], state["user_query"], response)

    return state
