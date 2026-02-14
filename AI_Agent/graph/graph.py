import time
import logging

from AI_Agent.graph.nodes.apply import apply_node
from AI_Agent.graph.nodes.expansion import expansion_node
from AI_Agent.graph.nodes.file_loader import file_loader_node
from AI_Agent.graph.nodes.intent import intent_node
from AI_Agent.graph.nodes.planner import planner_node
from AI_Agent.graph.nodes.propose import propose_node
from AI_Agent.graph.nodes.reasoning import reasoning_node
from AI_Agent.graph.nodes.retrieval import retrieval_node
from AI_Agent.graph.state import AgentState
from AI_Agent.memory.store import memory
from AI_Agent.utils.logger import get_logger


orch_logger = get_logger("OrchestrationAgent")
intent_logger = get_logger("IntentAgent")
plan_logger = get_logger("PlanningAgent")
rag_logger = get_logger("RAGAgent")
route_logger = get_logger("RoutingAgent")
apply_logger = get_logger("ApplyAgent")
reason_logger = get_logger("ReasoningAgent")
propose_logger = get_logger("ProposeAgent")


logger = logging.getLogger("ai_agent.orchestrator")


class OrchestratorGraph:
    """
    Lightweight orchestrator that coordinates the full agent pipeline.

    Flow:
      1) intent classification
      2) planning
      3) retrieval from RAG index
      4) rulebook-gated context expansion
      5) optional full-file loading
      6) route to reasoning (Q&A) or propose (code change) node
      7) for code changes, require explicit user approval before apply/push
    """

    @staticmethod
    def _is_approval_query(text: str) -> bool:
        normalized = text.strip().lower()
        return normalized in {"approve", "approved", "yes push", "approve changes", "yes"}

    def invoke(self, state: AgentState) -> AgentState:

        start_total = time.time()

        orch_logger.info("=" * 90)
        orch_logger.info("OrchestrationAgent -> Workflow started")
        orch_logger.info(f"Session ID: {state.get('session_id')}")
        orch_logger.info(f'User asked: "{state.get("user_query")}"')
        orch_logger.info("=" * 90)

        session_id = state.get("session_id")

        # ===================== APPROVAL FLOW =====================

        if session_id and self._is_approval_query(state["user_query"]):

            orch_logger.info("OrchestrationAgent -> Approval flow triggered")

            pending = memory.get_pending_diff(session_id)
            if not pending:
                orch_logger.warning(
                    "OrchestrationAgent -> No pending changes found for approval"
        session_id = state.get("session_id")

        if session_id and self._is_approval_query(state["user_query"]):
            logger.info(
                "session=%s step=approval_check status=approval_query_detected",
                session_id,
            )
            pending = memory.get_pending_diff(session_id)
            if not pending:
                logger.info(
                    "session=%s step=approval_check status=no_pending_diff", session_id
                )
                state["explanation"] = "No pending proposed changes found to approve."
                return state

            state["proposed_diff_id"] = pending.bundle_id
            state["approved"] = True

            try:
                apply_start = time.time()
                apply_logger.info("ApplyAgent -> Applying approved changes...")
                state = apply_node(state)
                memory.clear_pending_diff(session_id)
                memory.add_turn(session_id, state["user_query"], state["explanation"])
                apply_logger.info(
                    f"ApplyAgent -> Changes applied successfully "
                    f"(duration={round(time.time()-apply_start,3)}s)"
                )
            except Exception as exc:
                apply_logger.error(
                    f"ApplyAgent -> Apply/push failed: {exc}"
                )
                state["explanation"] = f"Approval received, but apply/push failed: {exc}"

            return state

        # ===================== INTENT =====================

        intent_logger.info("IntentAgent -> Analyzing user intent...")
        intent_start = time.time()
        state = intent_node(state)
        intent_logger.info(
            f"IntentAgent -> Intent classified as: {state['intent']} "
            f"(duration={round(time.time()-intent_start,3)}s)"
        )

        # ===================== PLANNING =====================

        plan_logger.info("PlanningAgent -> Creating execution strategy...")
        plan_start = time.time()
        state = planner_node(state)
        plan_logger.info(
            f"PlanningAgent -> Plan created successfully "
            f"(duration={round(time.time()-plan_start,3)}s)"
        )

        # ===================== RETRIEVAL =====================

        rag_logger.info("RAGAgent -> Querying vector store for relevant chunks...")
        rag_start = time.time()
        state = retrieval_node(state)

        retrieved_count = len(state.get("retrieved_chunks", []))
        rag_logger.info(
            f"RAGAgent -> Retrieved {retrieved_count} chunks "
            f"(duration={round(time.time()-rag_start,3)}s)"
        )

        # ===================== EXPANSION =====================

        # Expansion logs handled inside expansion_node
        state = expansion_node(state)

        # ===================== FILE LOADING =====================

        orch_logger.info("OrchestrationAgent -> Loading additional full files if required...")
        file_start = time.time()
        state = file_loader_node(state)
        orch_logger.info(
            f"OrchestrationAgent -> File loading completed "
            f"(duration={round(time.time()-file_start,3)}s)"
        )

        # ===================== ROUTING =====================

        route_logger.info("RoutingAgent -> Determining execution path...")

        if state["intent"].value in {"Modify", "Refactor", "Debug"}:
            route_logger.info("RoutingAgent -> Routed to ProposeAgent")
            propose_start = time.time()
            result = propose_node(state)
            propose_logger.info(
                f"ProposeAgent -> Proposal generated "
                f"(duration={round(time.time()-propose_start,3)}s)"
            )
        else:
            route_logger.info("RoutingAgent -> Routed to ReasoningAgent")
            reason_start = time.time()
            result = reasoning_node(state)
            reason_logger.info(
                f"ReasoningAgent -> Response generated "
                f"(duration={round(time.time()-reason_start,3)}s)"
            )

        orch_logger.info(
            f"OrchestrationAgent -> Workflow completed "
            f"(total_duration={round(time.time()-start_total,3)}s)"
        )
        orch_logger.info("=" * 90)

        return result
                logger.info(
                    "session=%s step=apply_node status=start proposed_diff_id=%s",
                    session_id,
                    pending.bundle_id,
                )
                state = apply_node(state)
                logger.info(
                    "session=%s step=apply_node status=done proposed_diff_id=%s",
                    session_id,
                    pending.bundle_id,
                )
                memory.clear_pending_diff(session_id)
                memory.add_turn(session_id, state["user_query"], state["explanation"])
            except Exception as exc:
                logger.exception(
                    "session=%s step=apply_node status=error error=%s",
                    session_id,
                    exc,
                )
                state["explanation"] = f"Approval received, but apply/push failed: {exc}"
            return state

        # Orchestration stage 1–5: gather and refine context safely.
        logger.info(
            "session=%s step=intent_node status=start user_query=%r",
            session_id,
            state.get("user_query"),
        )
        state = intent_node(state)
        logger.info(
            "session=%s step=intent_node status=done intent=%s",
            session_id,
            getattr(state.get("intent"), "value", state.get("intent")),
        )

        logger.info("session=%s step=planner_node status=start", session_id)
        state = planner_node(state)
        logger.info("session=%s step=planner_node status=done", session_id)

        logger.info("session=%s step=retrieval_node status=start", session_id)
        state = retrieval_node(state)
        logger.info(
            "session=%s step=retrieval_node status=done retrieved_chunks=%d",
            session_id,
            len(state.get("retrieved_chunks") or []),
        )

        logger.info("session=%s step=expansion_node status=start", session_id)
        state = expansion_node(state)
        logger.info(
            "session=%s step=expansion_node status=done expanded_chunks=%d",
            session_id,
            len(state.get("expanded_chunks") or []),
        )

        logger.info("session=%s step=file_loader_node status=start", session_id)
        state = file_loader_node(state)
        logger.info(
            "session=%s step=file_loader_node status=done file_chunks=%d",
            session_id,
            len(state.get("file_chunks") or []),
        )

        # Orchestration stage 6: route by intent family.
        if state["intent"].value in {"Modify", "Refactor", "Debug"}:
            logger.info(
                "session=%s step=propose_node status=start intent=%s",
                session_id,
                state["intent"].value,
            )
            return propose_node(state)

        logger.info(
            "session=%s step=reasoning_node status=start intent=%s",
            session_id,
            getattr(state.get("intent"), "value", state.get("intent")),
        )
        return reasoning_node(state)


def build_graph():
    return OrchestratorGraph()
