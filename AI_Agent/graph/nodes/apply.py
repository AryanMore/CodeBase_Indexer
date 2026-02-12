# graph/nodes/apply.py
from AI_Agent.graph.state import AgentState
from AI_Agent.tools.git_ops import GitClient


git = GitClient()


def apply_node(state: AgentState) -> AgentState:
    if not state.get("approved"):
        raise RuntimeError("Cannot apply changes without approval")

    git.apply_changes(state["proposed_diff_id"])
    return state
