from AI_Agent.graph.state import AgentState
from AI_Agent.tools.git_ops import GitClient


git = GitClient()


def apply_node(state: AgentState) -> AgentState:
    if not state.get("approved"):
        raise RuntimeError("Cannot apply changes without approval")

    diff_id = state.get("proposed_diff_id")
    if not diff_id:
        raise RuntimeError("No proposed diff to apply")

    git.apply_changes(diff_id)
    branch = git.commit_and_push("Apply AI Agent approved changes")
    state["explanation"] = f"Changes applied, committed, and pushed to origin/{branch}."
    return state
