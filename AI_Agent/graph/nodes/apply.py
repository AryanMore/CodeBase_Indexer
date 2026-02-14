from AI_Agent.graph.state import AgentState
from AI_Agent.memory.store import memory
from AI_Agent.tools.git_ops import GitClient, resolve_repo_root_for_url


def apply_node(state: AgentState) -> AgentState:
    if not state.get("approved"):
        raise RuntimeError("Cannot apply changes without approval")

    session_id = state.get("session_id")
    pending = memory.get_pending_diff(session_id) if session_id else None
    if not pending:
        raise RuntimeError("No proposed diff to apply")

    repo_url = state.get("repo_url") or ""
    repo_root = resolve_repo_root_for_url(repo_url)
    git = GitClient(repo_root=str(repo_root))

    git.apply_bundle(pending)
    branch = git.commit_and_push("Apply AI Agent approved changes")
    state["explanation"] = (
        f"Changes applied to {repo_url} at {repo_root}, "
        f"committed, and pushed to origin/{branch}."
    )
    return state
