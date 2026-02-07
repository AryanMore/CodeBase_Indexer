# graph/nodes/expansion.py
from graph.state import AgentState
from tools.rag import RAGClient
from rulebook.validator import RulebookValidator, RulebookViolation


rag = RAGClient()
validator = RulebookValidator()


def expansion_node(state: AgentState) -> AgentState:
    plan = state["plan"]

    if not plan or not plan.requires_expansion:
        return state

    source_chunks = state["retrieved_chunks"]
    source_ids = [c.chunk_id for c in source_chunks]

    requested_code_types = ["py:imports", "py:class_header"]
    scope = "same_file"
    max_chunks = 3

    # 🔒 RULEBOOK CHECK
    try:
        validator.validate_expansion(
            intent=state["intent"],
            source_chunks=source_chunks,
            requested_code_types=requested_code_types,
            scope=scope,
            max_chunks=max_chunks,
        )
    except RulebookViolation as e:
        # Fail closed: no expansion
        state["expanded_chunks"] = []
        state["explanation"] = str(e)
        return state

    expanded = rag.expand_context(
        source_chunk_ids=source_ids,
        requested_code_types=requested_code_types,
        scope=scope,
        max_chunks=max_chunks,
    )

    state["expanded_chunks"] = expanded
    return state
