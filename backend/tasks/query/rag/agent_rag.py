from __future__ import annotations

import heapq
import os
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

CANDIDATE_META_FIELDS = ["file_path", "chunk_type", "identifier", "uses", "class_name", "chunk_number"]
SCROLL_LIMIT = 256
MAX_EXPAND_SCAN_POINTS = int(os.getenv("MAX_EXPAND_SCAN_POINTS", "1200"))
RANKING_POOL_MULTIPLIER = 8
MIN_RANKING_POOL = 24


@dataclass
class SourceMeta:
    file_paths: Set[str]
    entries: List[Dict[str, Any]]

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


def _build_same_file_filter(
    file_paths: Set[str],
    repo_url: Optional[str],
    allowed_chunk_types: Optional[Set[str]] = None,
) -> Optional[Filter]:
    if not file_paths:
        return None

    must = [
        FieldCondition(key="file_path", match=MatchAny(any=list(file_paths)))
    ]

    if repo_url:
        must.append(FieldCondition(key="repo_url", match=MatchValue(value=repo_url)))

    if allowed_chunk_types:
        must.append(
            FieldCondition(key="chunk_type", match=MatchAny(any=list(allowed_chunk_types)))
        )

    return Filter(must=must)


def _fetch_points_for_same_files(
    file_paths: Set[str],
    repo_url: Optional[str],
    allowed_chunk_types: Optional[Set[str]] = None,
) -> List[Any]:

    if not file_paths:
        return []

    client = get_qdrant_client()

    query_filter = _build_same_file_filter(
        file_paths=file_paths,
        repo_url=repo_url,
        allowed_chunk_types=allowed_chunk_types,
    )

    result = client.scroll(
        collection_name=get_collection_name(),
        limit=SCROLL_LIMIT,
        scroll_filter=query_filter,
        with_payload=True,
    )

    return result[0]



def _fetch_points_for_same_files(
    file_paths: Set[str],
    repo_url: Optional[str],
    allowed_chunk_types: Optional[Set[str]] = None,
    payload_fields: Optional[List[str]] = None,
    max_points: Optional[int] = None,
) -> List[Any]:
    scroll_filter = _build_same_file_filter(file_paths, repo_url, allowed_chunk_types)
    if scroll_filter is None:
        return []

    client = get_qdrant_client()
    all_points: List[Any] = []
    offset = None
    with_payload = payload_fields if payload_fields else True

    while True:
        points, offset = client.scroll(
            collection_name=get_collection_name(),
            scroll_filter=scroll_filter,
            with_payload=with_payload,
            with_vectors=False,
            limit=SCROLL_LIMIT,
            offset=offset,
        )
        all_points.extend(points)
        if max_points is not None and len(all_points) >= max_points:
            return all_points[:max_points]
        if offset is None:
            break

    return all_points


def _prepare_source_meta(source_points: Iterable[Any]) -> SourceMeta:
    entries: List[Dict[str, Any]] = []
    file_paths: Set[str] = set()

    for sp in source_points:
        payload = sp.payload or {}
        file_path = payload.get("file_path")
        if file_path:
            file_paths.add(file_path)

        entries.append(
            {
                "identifier": payload.get("identifier"),
                "uses": set(payload.get("uses", []) or []),
                "class_name": payload.get("class_name"),
                "chunk_number": payload.get("chunk_number"),
            }
        )

    return SourceMeta(file_paths=file_paths, entries=entries)


def _relation_score(source_meta: SourceMeta, candidate_payload: Dict[str, Any]) -> float:
    score = 0.0

    if candidate_payload.get("file_path") in source_meta.file_paths:
        score += 2.0

    c_identifier = candidate_payload.get("identifier")
    c_uses = set(candidate_payload.get("uses", []) or [])
    c_class = candidate_payload.get("class_name")
    c_chunk_no = candidate_payload.get("chunk_number")

    for src in source_meta.entries:
        if c_identifier and c_identifier in src["uses"]:
            score += 3.0

        s_identifier = src["identifier"]
        if s_identifier and s_identifier in c_uses:
            score += 2.0

        if c_class and c_class == src["class_name"]:
            score += 1.5

        s_chunk_no = src["chunk_number"]
        if isinstance(c_chunk_no, int) and isinstance(s_chunk_no, int):
            dist = abs(c_chunk_no - s_chunk_no)
            if dist <= 2:
                score += (2 - min(dist, 2)) * 0.5

    return score


def _top_candidate_ids(
    candidates: Iterable[Any],
    source_meta: SourceMeta,
    source_ids: Set[str],
    max_chunks: int,
) -> List[str]:
    pool_size = max(MIN_RANKING_POOL, max_chunks * RANKING_POOL_MULTIPLIER)
    heap: List[tuple[float, str]] = []

    for point in candidates:
        pid = str(point.id)
        if pid in source_ids:
            continue

        score = _relation_score(source_meta, point.payload or {})
        if score <= 0:
            continue

        entry = (score, pid)
        if len(heap) < pool_size:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)

    heap.sort(reverse=True)
    return [pid for _, pid in heap[:max_chunks]]


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
        with_payload=CANDIDATE_META_FIELDS,
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

    source_meta = _prepare_source_meta(source_points)
    if scope == "same_file":
        candidates = _fetch_points_for_same_files(
            source_meta.file_paths,
            repo_url,
            allowed_chunk_types,
            payload_fields=CANDIDATE_META_FIELDS,
            max_points=MAX_EXPAND_SCAN_POINTS,
        )
    else:
        candidates = _fetch_points_for_same_files(
            source_meta.file_paths,
            repo_url,
            allowed_chunk_types,
            payload_fields=CANDIDATE_META_FIELDS,
            max_points=MAX_EXPAND_SCAN_POINTS,
        )

    source_ids = {str(p.id) for p in source_points}
    top_ids = _top_candidate_ids(candidates, source_meta, source_ids, max_chunks)
    if not top_ids:
        return []

    top_points = client.retrieve(
        collection_name=get_collection_name(),
        ids=top_ids,
        with_payload=True,
        with_vectors=False,
    )
    by_id = {str(point.id): point for point in top_points}
    ordered = [by_id[pid] for pid in top_ids if pid in by_id]

    return [_normalize_chunk(point) for point in ordered]
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
