import logging
import uuid

from AI_Agent.graph.graph import build_graph
from AI_Agent.memory.store import memory


# Configure logger
logger = logging.getLogger("ai_agent")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def run_agent(user_query: str, repo_url: str, session_id: str | None = None):
    """
    Runs the agent graph with conversational memory support.
    """

    # 🔹 Ensure session_id exists
    session_id = session_id or str(uuid.uuid4())

    # 🔹 Load previous conversation history
    previous_history = memory.get_history(session_id)

    # 🔹 Build graph
    graph = build_graph()

    # 🔹 Construct initial state
    initial_state = {
        "user_query": user_query,
        "repo_url": repo_url,
        "session_id": session_id,
        "chat_history": previous_history,  # ✅ conversational memory injected
        "intent": None,
        "plan": None,
        "retrieved_chunks": [],
        "expanded_chunks": [],
        "file_chunks": [],
        "explanation": None,
        "proposed_diff_id": None,
        "approved": False,
    }

<<<<<<< HEAD
    return graph.invoke(initial_state)
=======
    logger.info(
        "session=%s agent_run_start user_query=%r repo_url=%s",
        session_id,
        user_query,
        repo_url,
    )

    # 🔹 Run agent graph
    state = graph.invoke(initial_state)

    explanation = state.get("explanation") or ""

    # 🔹 Store turn in memory
    if explanation:
        memory.add_turn(session_id, user_query, explanation)

    logger.info(
        "session=%s agent_run_end intent=%s approved=%s",
        session_id,
        getattr(state.get("intent"), "value", state.get("intent")),
        state.get("approved"),
    )

    return state
>>>>>>> origin/memory-work


if __name__ == "__main__":
    repo = input("GitHub repo URL: ")
    query = input("Ask the agent: ")
    result = run_agent(query, repo)
    print(result)
