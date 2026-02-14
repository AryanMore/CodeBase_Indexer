from AI_Agent.tools.rag import RAGClient


def test_retrieve_chunks_uses_internal_path(monkeypatch):
    client = RAGClient()
    client.BASE_URL = "http://localhost:8000"
    client.USE_INTERNAL_RAG = True

    monkeypatch.setattr(
        "backend.tasks.query.rag.agent_rag.retrieve_chunks_for_agent",
        lambda query, top_k, repo_url: [
            {
                "chunk_id": "1",
                "file_path": "a.py",
                "content": "def x(): pass",
                "code_type": "py:function",
                "start_line": 1,
                "end_line": 1,
                "symbols": ["x"],
            }
        ],
    )

    chunks = client.retrieve_chunks("what?", 5, "https://github.com/example/repo")
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "1"


def test_expand_context_uses_internal_path(monkeypatch):
    client = RAGClient()
    client.BASE_URL = "http://localhost:8000"
    client.USE_INTERNAL_RAG = True

    monkeypatch.setattr(
        "backend.tasks.query.rag.agent_rag.expand_context_for_agent",
        lambda repo_url, source_chunk_ids, requested_code_types, scope, max_chunks: [
            {
                "chunk_id": "2",
                "file_path": "b.py",
                "content": "import os",
                "code_type": "py:imports",
                "start_line": 1,
                "end_line": 1,
                "symbols": None,
            }
        ],
    )

    chunks = client.expand_context(
        repo_url="https://github.com/example/repo",
        source_chunk_ids=["1"],
        requested_code_types=["py:imports"],
        scope="same_file",
        max_chunks=3,
    )
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "2"
