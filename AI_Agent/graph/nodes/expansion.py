from AI_Agent.graph.state import AgentState
from AI_Agent.rulebook.validator import RulebookValidator, RulebookViolation
from AI_Agent.tools.rag import RAGClient
from AI_Agent.utils.logger import get_logger

expand_logger = get_logger("ContextExpansionAgent")
import os

from AI_Agent.graph.state import AgentState
from AI_Agent.rulebook.validator import RulebookValidator, RulebookViolation
from AI_Agent.tools.rag import RAGClient

rag = RAGClient()
validator = RulebookValidator()


# Global expansion controls (per query), aligned with policy/plan.md.
EXPANSION_BUDGET = int(os.getenv("EXPANSION_BUDGET", "4"))
MAX_EXPANSION_DEPTH = int(os.getenv("MAX_EXPANSION_DEPTH", "1"))

DEFAULT_EXPANSION_TYPES = ["py:imports", "py:class_header"]


def _requested_code_types(state: AgentState) -> list[str]:
    retrieved_types = [c.code_type for c in state.get("retrieved_chunks", []) if c.code_type]

    if any(t == "py:function" for t in retrieved_types):
        return ["py:imports", "py:class_header"]

    if any(t in {"js:class_header", "js:function"} for t in retrieved_types):
        return ["js:function"]

    return DEFAULT_EXPANSION_TYPES


def expansion_node(state: AgentState) -> AgentState:

    expand_logger.info("ContextExpansionAgent -> Starting context expansion process")

    plan = state["plan"]

    if not plan or not plan.requires_expansion:
        expand_logger.info("ContextExpansionAgent -> Expansion not required by plan")
    plan = state["plan"]

    if not plan or not plan.requires_expansion:
        return state

    # Budget/depth guard: this implementation supports a single expansion hop per query.
    # If the configured budget is exhausted (or disabled via 0), skip expansion and
    # let downstream reasoning work with the initial retrieved chunks only.
    if EXPANSION_BUDGET <= 0 or MAX_EXPANSION_DEPTH <= 0:
        state["expanded_chunks"] = []
        # Do NOT overwrite an existing explanation if one is already present.
        if not state.get("explanation"):
            state["explanation"] = (
                "Expansion budget or depth limit is exhausted for this query. "
                "Answering using only the initially retrieved chunks. "
                "If the answer seems incomplete, more context may be required."
            )
        return state

    source_chunks = state["retrieved_chunks"]
    source_ids = [c.chunk_id for c in source_chunks]

    expand_logger.info(
        f"ContextExpansionAgent -> Initial chunk count: {len(source_chunks)}"
    )

    if not source_ids:
        expand_logger.info(
            "ContextExpansionAgent -> No source chunk IDs available for expansion"
        )
    if not source_ids:
        state["expanded_chunks"] = []
        return state

    requested_code_types = _requested_code_types(state)
    scope = "same_file"
    max_chunks = 3

    expand_logger.info(
        f"ContextExpansionAgent -> Requested code types: {requested_code_types}"
    )
    expand_logger.info(
        f"ContextExpansionAgent -> Scope: {scope} | Max chunks: {max_chunks}"
    )

    # ---------------- VALIDATION ----------------

    expand_logger.info(
        "ContextExpansionAgent -> Validating expansion request against rulebook"
    )

    try:
        validator.validate_expansion(
            intent=state["intent"],
            source_chunks=source_chunks,
            requested_code_types=requested_code_types,
            scope=scope,
            max_chunks=max_chunks,
        )
        expand_logger.info(
            "ContextExpansionAgent -> Rulebook validation successful"
        )
    except RulebookViolation as e:
        expand_logger.warning(
            f"ContextExpansionAgent -> Rulebook violation: {str(e)}"
        )
    except RulebookViolation as e:
        state["expanded_chunks"] = []
        state["explanation"] = str(e)
        return state

    # ---------------- EXPANSION ----------------

    expand_logger.info(
        f"ContextExpansionAgent -> Expanding context for chunk IDs: {source_ids}"
    )

    expanded = rag.expand_context(
        repo_url=state["repo_url"],
        source_chunk_ids=source_ids,
        requested_code_types=requested_code_types,
        scope=scope,
        max_chunks=max_chunks,
    )

    expand_logger.info(
        f"ContextExpansionAgent -> Retrieved {len(expanded)} expanded chunks"
    )

    expand_logger.info(
        f"ContextExpansionAgent -> Expansion complete "
        f"({len(source_chunks)} -> {len(source_chunks) + len(expanded)}) total chunks"
    )

    state["expanded_chunks"] = expanded

    return state

    state["expanded_chunks"] = expanded
    return state
