from AI_Agent.graph.state import AgentState
from AI_Agent.memory.store import summarize_history
from AI_Agent.tools.rag import RAGClient

rag = RAGClient()


def retrieval_node(state: AgentState) -> AgentState:
    # Context expansion starts at retrieval time by enriching the query with
    # a compact memory summary from previous turns in the same session.
    history = summarize_history(state.get("session_id"))
    query = state["user_query"] if not history else f"{history}\n\nCurrent query: {state['user_query']}"

    # Retrieve top-k semantic chunks from the shared backend RAG service.
    chunks = rag.retrieve_chunks(
        query=query,
        top_k=5,
        repo_url=state["repo_url"],
    )

    state["retrieved_chunks"] = chunks
    return state
