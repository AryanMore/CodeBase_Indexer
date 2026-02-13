from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set

from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

from backend.infra.db import get_collection_name, get_qdrant_client
from backend.infra.llm import embed_text


CHUNK_TYPE_TO_CODE_TYPE = {
    "python_import": "py:imports",
    "python_class_header": "py:class_header",
    "python_class_function": "py:function",
    "python_function": "py:function",
    "python_docstring": "py:docstring",
    "python_top_level_code": "py:top_level",
    "javascript_import": "js:imports",
    "javascript_class_header": "js:class_header",
    "javascript_class_function": "js:function",
    "javascript_function": "js:function",
    "javascript_top_level_code": "js:top_level",
    "html_main": "html:main",
    "html_section": "html:section",
    "html_article": "html:article",
    "html_nav": "html:nav",
    "html_form": "html:form",
    "html_header": "html:header",
    "html_footer": "html:footer",
    "html_top_level_markup": "html:top_level",
    "blind_chunk": "text:chunk",
}

CODE_TYPE_TO_CHUNK_TYPES = {
    "py:imports": {"python_import"},
    "py:class_header": {"python_class_header"},
    "py:function": {"python_function", "python_class_function"},
    "py:docstring": {"python_docstring"},
    "js:imports": {"javascript_import"},
    "js:class_header": {"javascript_class_header"},
    "js:function": {"javascript_function", "javascript_class_function"},
    "html:section": {"html_section"},
    "html:article": {"html_article"},
    "html:main": {"html_main"},
}


@dataclass
class Candidate:
    point: Any
    score: float


def _repo_filter(repo_url: Optional[str]) -> Optional[Filter]:
    if not repo_url:
        return None
    return Filter(must=[FieldCondition(key="repo_url", match=MatchValue(value=repo_url))])


def _normalize_chunk(point: Any) -> Dict[str, Any]:
    payload = point.payload or {}
    content = payload.get("content", "")
    start_line = 1 if content else None
    end_line = len(content.splitlines()) if content else None

    symbols = []
    for key in ("identifier", "class_name"):
        if payload.get(key):
            symbols.append(payload[key])

    return {
        "chunk_id": str(point.id),
        "file_path": payload.get("file_path", ""),
        "content": content,
        "code_type": CHUNK_TYPE_TO_CODE_TYPE.get(payload.get("chunk_type")),
        "start_line": start_line,
        "end_line": end_line,
        "symbols": symbols or None,
    }


def retrieve_chunks_for_agent(query: str, top_k: int, repo_url: Optional[str]) -> List[Dict[str, Any]]:
    client = get_qdrant_client()
    result = client.query_points(
        collection_name=get_collection_name(),
        query=embed_text(query),
        limit=top_k,
        query_filter=_repo_filter(repo_url),
    )
    return [_normalize_chunk(point) for point in result.points]


def _fetch_points_for_same_files(file_paths: Set[str], repo_url: Optional[str]) -> List[Any]:
    if not file_paths:
        return []

    must = [FieldCondition(key="file_path", match=MatchAny(any=list(file_paths)))]
    if repo_url:
        must.append(FieldCondition(key="repo_url", match=MatchValue(value=repo_url)))

    client = get_qdrant_client()
    all_points: List[Any] = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=get_collection_name(),
            scroll_filter=Filter(must=must),
            with_payload=True,
            with_vectors=False,
            limit=256,
            offset=offset,
        )
        all_points.extend(points)
        if offset is None:
            break

    return all_points


def _relation_score(source_points: Iterable[Any], candidate: Any) -> float:
    score = 0.0
    cp = candidate.payload or {}

    source_by_file = {((p.payload or {}).get("file_path")) for p in source_points}
    if cp.get("file_path") in source_by_file:
        score += 2.0

    c_identifier = cp.get("identifier")
    c_uses = set(cp.get("uses", []) or [])
    c_class = cp.get("class_name")
    c_chunk_no = cp.get("chunk_number")

    for sp in source_points:
        sp_payload = sp.payload or {}
        s_uses = set(sp_payload.get("uses", []) or [])

        if c_identifier and c_identifier in s_uses:
            score += 3.0

        s_identifier = sp_payload.get("identifier")
        if s_identifier and s_identifier in c_uses:
            score += 2.0

        if c_class and c_class == sp_payload.get("class_name"):
            score += 1.5

        s_chunk_no = sp_payload.get("chunk_number")
        if isinstance(c_chunk_no, int) and isinstance(s_chunk_no, int):
            dist = abs(c_chunk_no - s_chunk_no)
            if dist <= 2:
                score += (2 - min(dist, 2)) * 0.5

    return score


def expand_context_for_agent(
    repo_url: Optional[str],
    source_chunk_ids: List[str],
    requested_code_types: List[str],
    scope: str,
    max_chunks: int,
) -> List[Dict[str, Any]]:
    client = get_qdrant_client()
    source_points = client.retrieve(
        collection_name=get_collection_name(),
        ids=source_chunk_ids,
        with_payload=True,
        with_vectors=False,
    )
    if not source_points:
        return []

    file_paths = {((p.payload or {}).get("file_path")) for p in source_points if (p.payload or {}).get("file_path")}
    if scope == "same_file":
        candidates = _fetch_points_for_same_files(file_paths, repo_url)
    else:
        candidates = _fetch_points_for_same_files(file_paths, repo_url)

    allowed_chunk_types: Set[str] = set()
    for code_type in requested_code_types:
        allowed_chunk_types.update(CODE_TYPE_TO_CHUNK_TYPES.get(code_type, set()))

    source_ids = {str(p.id) for p in source_points}
    scored: List[Candidate] = []
    for point in candidates:
        pid = str(point.id)
        if pid in source_ids:
            continue

        p_payload = point.payload or {}
        if allowed_chunk_types and p_payload.get("chunk_type") not in allowed_chunk_types:
            continue

        score = _relation_score(source_points, point)
        if score <= 0:
            continue
        scored.append(Candidate(point=point, score=score))

    scored.sort(key=lambda c: c.score, reverse=True)
    return [_normalize_chunk(c.point) for c in scored[:max_chunks]]
