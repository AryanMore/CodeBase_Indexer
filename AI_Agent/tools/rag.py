import os

import requests

from AI_Agent.schemas.chunk import Chunk


class RAGClient:
    BASE_URL = os.getenv("RAG_BASE_URL", "http://localhost:8000")
    USE_INTERNAL_RAG = os.getenv("USE_INTERNAL_RAG", "true").lower() == "true"

    def _can_use_internal(self) -> bool:
        return self.USE_INTERNAL_RAG and self.BASE_URL in {"http://localhost:8000", "http://127.0.0.1:8000"}

    def retrieve_chunks(self, query: str, top_k: int, repo_url: str):
        if self._can_use_internal():
            from backend.tasks.query.rag.agent_rag import retrieve_chunks_for_agent

            chunks = retrieve_chunks_for_agent(query=query, top_k=top_k, repo_url=repo_url)
            return [Chunk(**c) for c in chunks]


    def retrieve_chunks(self, query: str, top_k: int, repo_url: str):
        response = requests.post(
            f"{self.BASE_URL}/rag/retrieve",
            json={"repo_url": repo_url, "query": query, "top_k": top_k},
            timeout=60,
        )
        response.raise_for_status()
        return [Chunk(**c) for c in response.json()["chunks"]]

    def expand_context(
        self,
        repo_url: str,
        source_chunk_ids: list[str],
        requested_code_types: list[str],
        scope: str,
        max_chunks: int,
    ):
        if self._can_use_internal():
            from backend.tasks.query.rag.agent_rag import expand_context_for_agent

            chunks = expand_context_for_agent(
                repo_url=repo_url,
                source_chunk_ids=source_chunk_ids,
                requested_code_types=requested_code_types,
                scope=scope,
                max_chunks=max_chunks,
            )
            return [Chunk(**c) for c in chunks]

        response = requests.post(
            f"{self.BASE_URL}/rag/expand",
            json={
                "repo_url": repo_url,
                "source_chunk_ids": source_chunk_ids,
                "requested_code_types": requested_code_types,
                "scope": scope,
                "max_chunks": max_chunks,
            },
            timeout=60,
        )
        response.raise_for_status()
        return [Chunk(**c) for c in response.json()["chunks"]]
