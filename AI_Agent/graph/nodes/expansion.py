from AI_Agent.graph.state import AgentState
from AI_Agent.rulebook.validator import RulebookValidator, RulebookViolation
from AI_Agent.tools.rag import RAGClient

rag = RAGClient()
validator = RulebookValidator()


DEFAULT_EXPANSION_TYPES = ["py:imports", "py:class_header"]


def _requested_code_types(state: AgentState) -> list[str]:
    retrieved_types = [c.code_type for c in state.get("retrieved_chunks", []) if c.code_type]

    if any(t == "py:function" for t in retrieved_types):
        return ["py:imports", "py:class_header"]

    if any(t in {"js:class_header", "js:function"} for t in retrieved_types):
        return ["js:function"]

    return DEFAULT_EXPANSION_TYPES


def expansion_node(state: AgentState) -> AgentState:
    plan = state["plan"]

    if not plan or not plan.requires_expansion:
        return state

    source_chunks = state["retrieved_chunks"]
    source_ids = [c.chunk_id for c in source_chunks]
    if not source_ids:
        state["expanded_chunks"] = []
        return state

    requested_code_types = _requested_code_types(state)
    scope = "same_file"
    max_chunks = 3

    try:
        validator.validate_expansion(
            intent=state["intent"],
            source_chunks=source_chunks,
            requested_code_types=requested_code_types,
            scope=scope,
            max_chunks=max_chunks,
        )
    except RulebookViolation as e:
        state["expanded_chunks"] = []
        state["explanation"] = str(e)
        return state

    expanded = rag.expand_context(
        repo_url=state["repo_url"],
        source_chunk_ids=source_ids,
        requested_code_types=requested_code_types,
        scope=scope,
        max_chunks=max_chunks,
    )

    state["expanded_chunks"] = expanded
    return state
