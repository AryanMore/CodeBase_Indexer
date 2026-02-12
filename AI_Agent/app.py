import uuid

from AI_Agent.graph.graph import build_graph


def run_agent(user_query: str, repo_url: str, session_id: str | None = None):
    graph = build_graph()

    initial_state = {
        "user_query": user_query,
        "repo_url": repo_url,
        "session_id": session_id or str(uuid.uuid4()),
        "chat_history": [],
        "intent": None,
        "plan": None,
        "retrieved_chunks": [],
        "expanded_chunks": [],
        "file_chunks": [],
        "explanation": None,
        "proposed_diff_id": None,
        "approved": False,
    }

    return graph.invoke(initial_state)


if __name__ == "__main__":
    repo = input("GitHub repo URL: ")
    query = input("Ask the agent: ")
    result = run_agent(query, repo)
    print(result)
