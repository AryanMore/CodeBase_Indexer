import uuid

from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, render_prompt
from AI_Agent.memory.store import memory
from AI_Agent.schemas.diff import DiffBundle, FileDiff


def propose_node(state: AgentState) -> AgentState:
    approved_chunks = state["retrieved_chunks"] + state["expanded_chunks"] + state["file_chunks"]

    context = "\n\n".join(
        f"[{c.file_path}:{c.start_line}-{c.end_line}]\n{c.content}" for c in approved_chunks
    )

    prompt = render_prompt(
        "AI_Agent/prompts/propose.txt",
        {
            "context": context,
            "goal": state["user_query"],
        },
    )
    response = chat(prompt, max_tokens=450)

    bundle = DiffBundle(
        bundle_id=str(uuid.uuid4()),
        goal=state["user_query"],
        files=[FileDiff(file_path="MULTI_FILE", diff=response)],
        explanation="Generated from approved context only.",
    )

    state["proposed_diff_id"] = bundle.bundle_id
    state["explanation"] = response

    if state.get("session_id"):
        memory.add_turn(state["session_id"], state["user_query"], response)
    return state
