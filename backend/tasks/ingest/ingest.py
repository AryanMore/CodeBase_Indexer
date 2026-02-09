import shutil
from pathlib import Path

from backend.tasks.ingest.repo_clone.clone_repo import clone_repo
from backend.tasks.ingest.embedding.dispatcher import embed_file
from backend.tasks.ingest.vector_store.qdrant_store import insert_chunks
from backend.infra.db import clear_collection


ALLOWED_EXTENSIONS = {".md", ".txt", ".py", ".js", ".html"}
IGNORE_DIRS = {".git", "__pycache__", "node_modules", "venv"}


def ingest(repo_url: str) -> None:
    clear_collection()

    repo_path: Path | None = None

    try:
        repo_path = clone_repo(repo_url)

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            if any(part in IGNORE_DIRS for part in file_path.parts):
                continue

            if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue

            chunks = embed_file(file_path)
            if not chunks:
                continue

            relative_path = file_path.relative_to(repo_path)

            for chunk in chunks:
                chunk["file_path"] = str(relative_path)

            insert_chunks(chunks)

    finally:
        if repo_path and repo_path.exists():
            shutil.rmtree(repo_path, ignore_errors=True)
