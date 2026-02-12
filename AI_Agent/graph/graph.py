from AI_Agent.graph.nodes.expansion import expansion_node
from AI_Agent.graph.nodes.file_loader import file_loader_node
from AI_Agent.graph.nodes.intent import intent_node
from AI_Agent.graph.nodes.planner import planner_node
from AI_Agent.graph.nodes.propose import propose_node
from AI_Agent.graph.nodes.reasoning import reasoning_node
from AI_Agent.graph.nodes.retrieval import retrieval_node
from AI_Agent.graph.state import AgentState


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
    """

    def invoke(self, state: AgentState) -> AgentState:
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
