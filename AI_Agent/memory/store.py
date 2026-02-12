from typing import Optional


class AgentMemory:
    def __init__(self):
        self._state: dict[str, list[dict]] = {}

    def add_turn(self, session_id: str, user_query: str, response: str) -> None:
        self._state.setdefault(session_id, []).append(
            {"user_query": user_query, "response": response}
        )

    def get_history(self, session_id: str) -> list[dict]:
        return self._state.get(session_id, [])


memory = AgentMemory()


def summarize_history(session_id: Optional[str]) -> str:
    if not session_id:
        return ""
    turns = memory.get_history(session_id)[-3:]
    if not turns:
        return ""
    return "\n".join(f"User: {t['user_query']}\nAgent: {t['response']}" for t in turns)
