import os

import requests

from AI_Agent.schemas.chunk import Chunk


class RAGClient:
    BASE_URL = os.getenv("RAG_BASE_URL", "http://localhost:8000")

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
