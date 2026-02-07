# graph/graph.py
from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.nodes.intent import intent_node
from graph.nodes.planner import planner_node
from graph.nodes.retrieval import retrieval_node
from graph.nodes.expansion import expansion_node
from graph.nodes.file_loader import file_loader_node
from graph.nodes.reasoning import reasoning_node
from graph.nodes.propose import propose_node
from graph.nodes.apply import apply_node


def build_graph():
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("intent", intent_node)
    graph.add_node("planner", planner_node)
    graph.add_node("retrieve", retrieval_node)
    graph.add_node("expand", expansion_node)
    graph.add_node("file", file_loader_node)
    graph.add_node("reason", reasoning_node)
    graph.add_node("propose", propose_node)
    graph.add_node("apply", apply_node)

    # Entry
    graph.set_entry_point("intent")

    # Linear mandatory steps
    graph.add_edge("intent", "planner")
    graph.add_edge("planner", "retrieve")
    graph.add_edge("retrieve", "expand")
    graph.add_edge("expand", "file")

    # Conditional routing
    def route_after_context(state: AgentState):
        if state["intent"].value in {"Modify", "Refactor", "Debug"}:
            return "propose"
        return "reason"

    graph.add_conditional_edges(
        "file",
        route_after_context,
        {
            "propose": "propose",
            "reason": "reason",
        },
    )

    # End paths
    graph.add_edge("reason", END)
    graph.add_edge("propose", END)
    graph.add_edge("apply", END)

    return graph.compile()
