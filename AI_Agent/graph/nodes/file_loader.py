# graph/nodes/file_loader.py
from AI_Agent.graph.state import AgentState
from AI_Agent.tools.filesystem import FileSystemClient


fs = FileSystemClient()


def file_loader_node(state: AgentState) -> AgentState:
    plan = state["plan"]

    if not plan or not plan.requires_full_file:
        return state

    file_chunks = []
    for file_path in plan.target_files or []:
        file_chunks.extend(fs.get_file_chunks(file_path))

    state["file_chunks"] = file_chunks
    return state
