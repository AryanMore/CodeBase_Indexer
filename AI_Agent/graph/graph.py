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
            pending = memory.get_pending_diff(session_id)
            if not pending:
                state["explanation"] = "No pending proposed changes found to approve."
                return state

            state["proposed_diff_id"] = pending.bundle_id
            state["approved"] = True

            try:
                state = apply_node(state)
                memory.clear_pending_diff(session_id)
                memory.add_turn(session_id, state["user_query"], state["explanation"])
            except Exception as exc:
                state["explanation"] = f"Approval received, but apply/push failed: {exc}"
            return state

        # Orchestration stage 1–5: gather and refine context safely.
        state = intent_node(state)
        state = planner_node(state)
        state = retrieval_node(state)
        state = expansion_node(state)
        state = file_loader_node(state)

        # Orchestration stage 6: route by intent family.
        if state["intent"].value in {"Modify", "Refactor", "Debug"}:
            return propose_node(state)

        return reasoning_node(state)


def build_graph():
    return OrchestratorGraph()
