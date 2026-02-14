from types import SimpleNamespace

from backend.tasks.query.rag.agent_rag import (
    _build_same_file_filter,
    _normalize_chunk,
    _prepare_source_meta,
    _relation_score,
    _top_candidate_ids,
)


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
    source_points = [
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
    source_meta = _prepare_source_meta(source_points)

    candidate_payload = {
        "file_path": "svc.py",
        "identifier": "build_response",
        "uses": [],
        "chunk_number": 6,
    }

    far_candidate_payload = {
        "file_path": "other.py",
        "identifier": "noop",
        "uses": [],
        "chunk_number": 100,
    }

    assert _relation_score(source_meta, candidate_payload) > _relation_score(source_meta, far_candidate_payload)


def test_build_same_file_filter_applies_chunk_type_constraint():
    filt = _build_same_file_filter(
        file_paths={"svc.py"},
        repo_url="https://github.com/example/repo",
        allowed_chunk_types={"python_import", "python_class_header"},
    )

    assert filt is not None
    assert len(filt.must) == 3

    keys = {cond.key for cond in filt.must}
    assert keys == {"file_path", "repo_url", "chunk_type"}


def test_top_candidate_ids_returns_best_ranked_subset():
    source_points = [
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
    source_meta = _prepare_source_meta(source_points)

    candidates = [
        point("c1", {"file_path": "svc.py", "identifier": "build_response", "uses": [], "chunk_number": 6}),
        point("c2", {"file_path": "svc.py", "identifier": "noop", "uses": [], "chunk_number": 7}),
        point("c3", {"file_path": "other.py", "identifier": "noop", "uses": [], "chunk_number": 100}),
    ]

    top = _top_candidate_ids(candidates, source_meta, source_ids={"s1"}, max_chunks=2)

    assert top[0] == "c1"
    assert len(top) <= 2
