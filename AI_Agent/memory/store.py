from typing import Optional

from AI_Agent.schemas.diff import DiffBundle


class AgentMemory:
    def __init__(self):
        self._state: dict[str, list[dict]] = {}
        self._pending_diffs: dict[str, DiffBundle] = {}

    def add_turn(self, session_id: str, user_query: str, response: str) -> None:
        self._state.setdefault(session_id, []).append(
            {"user_query": user_query, "response": response}
        )

    def get_history(self, session_id: str) -> list[dict]:
        return self._state.get(session_id, [])

    def set_pending_diff(self, session_id: str, bundle: DiffBundle) -> None:
        self._pending_diffs[session_id] = bundle

    def get_pending_diff(self, session_id: str) -> Optional[DiffBundle]:
        return self._pending_diffs.get(session_id)

    def clear_pending_diff(self, session_id: str) -> None:
        self._pending_diffs.pop(session_id, None)


memory = AgentMemory()


def summarize_history(session_id: Optional[str]) -> str:
    if not session_id:
        return ""
    turns = memory.get_history(session_id)[-3:]
    if not turns:
        return ""
    return "\n".join(f"User: {t['user_query']}\nAgent: {t['response']}" for t in turns)
