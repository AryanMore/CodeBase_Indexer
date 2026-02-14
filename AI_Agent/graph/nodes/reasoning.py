from collections import defaultdict

from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, render_prompt
from AI_Agent.memory.store import memory


def _build_context(chunks):
    grouped = defaultdict(list)
    for c in chunks:
        grouped[c.file_path].append(c)

    sections = []
    for file_path, file_chunks in grouped.items():
        file_chunks.sort(key=lambda x: ((x.start_line or 0), (x.end_line or 0)))
        relations = []
        for c in file_chunks:
            label = c.code_type or "unknown"
            span = f"{c.start_line or '?'}-{c.end_line or '?'}"
            relations.append(f"{label}@{span}")

        body = "\n\n".join(
            f"[{c.file_path}:{c.start_line}-{c.end_line} | {c.code_type}]\n{c.content}"
            for c in file_chunks
        )
        sections.append(
            f"FILE: {file_path}\nRELATED CHUNKS: {', '.join(relations)}\n{body}"
        )

    return "\n\n".join(sections)


def _format_chat_history(history: list[dict]) -> str:
    if not history:
        return ""

    formatted = []
    for turn in history[-5:]:  # last 5 turns only
        formatted.append(f"User: {turn['user_query']}")
        formatted.append(f"Agent: {turn['response']}")

    return "\n".join(formatted)


def reasoning_node(state: AgentState) -> AgentState:
    approved_chunks = (
        state["retrieved_chunks"]
        + state["expanded_chunks"]
        + state["file_chunks"]
    )

    context = _build_context(approved_chunks)

    # 🔹 Format conversation history
    chat_history_str = "\n".join(
    f"User: {t['user_query']}\nAgent: {t['response']}"
    for t in state.get("chat_history", [])[-2:]
)


    prompt = render_prompt(
        "AI_Agent/prompts/reasoning.txt",
        {
            "context": context,
            "user_query": state["user_query"],
            "chat_history": chat_history_str,  # ✅ now injected
        },
    )

    response = chat(prompt)
    state["explanation"] = response

    return state
