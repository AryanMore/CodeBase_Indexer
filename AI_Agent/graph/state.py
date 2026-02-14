from typing import List, Optional, TypedDict

from AI_Agent.schemas.chunk import Chunk
from AI_Agent.schemas.intent import Intent
from AI_Agent.schemas.plan import Plan


class AgentState(TypedDict):
    user_query: str
    repo_url: str
    session_id: Optional[str]
    chat_history: List[dict]

    intent: Optional[Intent]
    plan: Optional[Plan]

    retrieved_chunks: List[Chunk]
    expanded_chunks: List[Chunk]
    file_chunks: List[Chunk]

    explanation: Optional[str]

    proposed_diff_id: Optional[str]
    approved: bool
