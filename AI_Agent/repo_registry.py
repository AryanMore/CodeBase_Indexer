from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def _mapping_file() -> Path:
    """
    Returns the path to the shared repo registry JSON file.

    This file lives at the project root so both the backend ingest
    pipeline and the AI agent can read/write it.
    """
    # This file is located at <project_root>/AI_Agent/repo_registry.py
    # so parents[1] is the project root directory.
    project_root = Path(__file__).resolve().parents[1]
    return project_root / ".repo_registry.json"


def _load_mapping() -> Dict[str, str]:
    path = _mapping_file()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")) or {}
    except Exception:
        # If the file is corrupted, fail gracefully and start fresh.
        return {}


def _save_mapping(mapping: Dict[str, str]) -> None:
    path = _mapping_file()
    path.write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")


def register_repo(repo_url: str, repo_path: Path) -> None:
    """
    Register or update the local checkout path for a given repo URL.

    The path should point at the root of a cloned git repository.
    """
    mapping = _load_mapping()
    mapping[repo_url] = str(Path(repo_path).resolve())
    _save_mapping(mapping)


def get_repo_path(repo_url: str) -> Optional[Path]:
    """
    Resolve the local checkout path for a given repo URL, if known.
    """
    mapping = _load_mapping()
    path_str = mapping.get(repo_url)
    if not path_str:
        return None
    return Path(path_str)

