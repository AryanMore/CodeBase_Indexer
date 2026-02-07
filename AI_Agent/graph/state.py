# graph/state.py
from typing import List, Optional, TypedDict
from schemas.intent import Intent
from schemas.chunk import Chunk
from schemas.plan import Plan


class AgentState(TypedDict):
    # User input
    user_query: str
    repo_url: str

    # Step 0
    intent: Optional[Intent]

    # Step 1
    plan: Optional[Plan]

    # Context
    retrieved_chunks: List[Chunk]
    expanded_chunks: List[Chunk]
    file_chunks: List[Chunk]

    # Outputs
    explanation: Optional[str]

    # Modify flow
    proposed_diff_id: Optional[str]
    approved: bool
