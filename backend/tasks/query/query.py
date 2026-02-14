from backend.tasks.query.rag.embed_query import embed_query
from backend.tasks.query.rag.retrieve import retrieve
from backend.tasks.query.answer.generate import generate_answer


def query_repo(question: str, top_k: int = 5) -> str:
    query_embedding = embed_query(question)
    retrieved_chunks = retrieve(query_embedding, top_k=top_k)
    return generate_answer(question, retrieved_chunks)
