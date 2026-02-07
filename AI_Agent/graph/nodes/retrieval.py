# graph/nodes/retrieval.py
from graph.state import AgentState
from tools.rag import RAGClient


rag = RAGClient()


def retrieval_node(state: AgentState) -> AgentState:
    chunks = rag.retrieve_chunks(
        query=state["user_query"],
        top_k=5,
    )

    state["retrieved_chunks"] = chunks
    return state
