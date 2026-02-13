from types import SimpleNamespace

from backend.tasks.query.rag.agent_rag import _normalize_chunk, _relation_score


def point(pid, payload):
    return SimpleNamespace(id=pid, payload=payload)


def test_normalize_chunk_maps_types_and_lines():
    p = point(
        "abc",
        {
            "file_path": "a.py",
            "content": "def x():\n    return 1",
            "chunk_type": "python_function",
            "identifier": "x",
        },
    )

    normalized = _normalize_chunk(p)
    assert normalized["chunk_id"] == "abc"
    assert normalized["code_type"] == "py:function"
    assert normalized["start_line"] == 1
    assert normalized["end_line"] == 2
    assert "x" in normalized["symbols"]


def test_relation_score_prefers_dependency_links():
    source = [
        point(
            "s1",
            {
                "file_path": "svc.py",
                "identifier": "handle",
                "uses": ["build_response"],
                "chunk_number": 5,
            },
        )
    ]

    candidate = point(
        "c1",
        {
            "file_path": "svc.py",
            "identifier": "build_response",
            "uses": [],
            "chunk_number": 6,
        },
    )

    far_candidate = point(
        "c2",
        {
            "file_path": "other.py",
            "identifier": "noop",
            "uses": [],
            "chunk_number": 100,
        },
    )

    assert _relation_score(source, candidate) > _relation_score(source, far_candidate)
