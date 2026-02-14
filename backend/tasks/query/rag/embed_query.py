from backend.infra.llm import embed_text


def embed_query(query: str) -> list:
    return embed_text(query)
