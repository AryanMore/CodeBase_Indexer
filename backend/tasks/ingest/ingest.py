import shutil
from pathlib import Path

from backend.tasks.ingest.repo_clone.clone_repo import clone_repo
from backend.tasks.ingest.embedding.dispatcher import process_repository
from backend.infra.db import clear_collection
from AI_Agent.repo_registry import register_repo


def ingest(repo_url: str) -> None:

    clear_collection()

    repo_path: Path | None = None

    try:
        repo_path = clone_repo(repo_url)

        process_repository(repo_path, repo_url=repo_url)

    finally:
        if repo_path and repo_path.exists():
            shutil.rmtree(repo_path, ignore_errors=True)
    repo_path = clone_repo(repo_url)

    # Index the repository into Qdrant.
    process_repository(repo_path, repo_url=repo_url)

    # Register the cloned repository path so the AI agent can later
    # apply and push changes against the correct working tree.
    register_repo(repo_url, repo_path)

