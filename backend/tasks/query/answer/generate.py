from backend.infra.llm import chat


def generate_answer(query: str, retrieved_chunks: list) -> str:
    context = "\n\n".join(
        f"File: {chunk['file_path']}\n{chunk['text']}"
        for chunk in retrieved_chunks
    )

    prompt = (
        "You are a helpful assistant answering questions about a GitHub repository.\n\n"
        "Global safety rules (apply ALWAYS):\n"
        "- If the user request is illegal, clearly harmful, or violates common safety policies "
        "(for example: serious crime, malware, personal data exfiltration, self-harm), you MUST refuse and "
        "answer with ONLY:\n"
        '- \"I cannot help with that request.\" \n'
        "- Do NOT provide workarounds, partial instructions, or alternatives that enable the harmful goal.\n\n"
        "Context (ground truth from the repository):\n"
        f"{context}\n\n"
        "Question:\n"
        f"{query}\n\n"
        "Answer concisely, grounded ONLY in the given context. "
        "If the context is insufficient, say what is missing instead of guessing."
    )

    return chat(prompt)
