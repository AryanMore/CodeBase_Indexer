import uuid

from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, render_prompt
from AI_Agent.memory.store import memory
from AI_Agent.schemas.diff import DiffBundle, FileDiff
from AI_Agent.tools.git_ops import GitClient


git = GitClient()


def _extract_patch(response: str) -> str:
    if "diff --git" in response:
        return response[response.index("diff --git"):]
    return response


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
    response = chat(prompt, max_tokens=650)

    bundle = DiffBundle(
        bundle_id=str(uuid.uuid4()),
        goal=state["user_query"],
        files=[FileDiff(file_path="MULTI_FILE", diff=_extract_patch(response))],
        explanation="Generated from approved context only.",
    )

    git.store_bundle(bundle)

    if state.get("session_id"):
        memory.set_pending_diff(state["session_id"], bundle)

    state["proposed_diff_id"] = bundle.bundle_id
    state["approved"] = False
    state["explanation"] = (
        f"Proposed changes ready (bundle_id={bundle.bundle_id}).\n\n"
        f"{response}\n\n"
        "If you want me to apply and push these changes to the repository, reply with: APPROVE"
    )

    if state.get("session_id"):
        memory.add_turn(state["session_id"], state["user_query"], state["explanation"])
    return state
