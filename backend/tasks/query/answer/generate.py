from backend.infra.llm import chat


def generate_answer(query: str, retrieved_chunks: list) -> str:
    context = "\n\n".join(
        f"File: {chunk['file_path']}\n{chunk['content']}"
        for chunk in retrieved_chunks
    )

    prompt = (
        "You are a helpful assistant answering questions about a GitHub repository.\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Question:\n"
        f"{query}\n\n"
        "Answer concisely:"
    )

    return chat(prompt)
