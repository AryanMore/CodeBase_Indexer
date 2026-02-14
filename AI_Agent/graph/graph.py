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
