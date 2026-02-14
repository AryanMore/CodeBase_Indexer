import os
from collections import defaultdict

from AI_Agent.graph.state import AgentState
from AI_Agent.infra.llm import chat, render_prompt
from AI_Agent.memory.store import memory

MAX_CONTEXT_CHARS_PER_CHUNK = int(os.getenv("MAX_CONTEXT_CHARS_PER_CHUNK", "1200"))
REASONING_MAX_TOKENS = int(os.getenv("REASONING_MAX_TOKENS", "180"))


def _clip(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated for latency]"


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
            f"[{c.file_path}:{c.start_line}-{c.end_line} | {c.code_type}]\n{_clip(c.content, MAX_CONTEXT_CHARS_PER_CHUNK)}"
            for c in file_chunks
        )
        sections.append(
            f"FILE: {file_path}\nRELATED CHUNKS: {', '.join(relations)}\n{body}"
        )

    return "\n\n".join(sections)


def reasoning_node(state: AgentState) -> AgentState:
    approved_chunks = state["retrieved_chunks"] + state["expanded_chunks"] + state["file_chunks"]
    context = _build_context(approved_chunks)

    prompt = render_prompt(
        "AI_Agent/prompts/reasoning.txt",
        {
            "context": context,
            "user_query": state["user_query"],
        },
    )

    response = chat(prompt, max_tokens=REASONING_MAX_TOKENS)
    state["explanation"] = response

    if state.get("session_id"):
        memory.add_turn(state["session_id"], state["user_query"], response)

    return state
