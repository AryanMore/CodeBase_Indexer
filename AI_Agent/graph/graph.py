import time
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


class OrchestratorGraph:
    """
    Lightweight orchestrator that coordinates the full agent pipeline.
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


def build_graph():
    return OrchestratorGraph()
