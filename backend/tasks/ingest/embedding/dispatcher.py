import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Set

from backend.infra.llm import embed_text
from backend.tasks.ingest.vector_store.qdrant_store import insert_chunks
from backend.tasks.ingest.embedding.blind_chunker import extract_chunks as fallback_extract


# -------------------------
# Dynamic Language Loader
# -------------------------

def load_language_modules():

    modules = []
    package_path = Path(__file__).parent

    for module_info in pkgutil.iter_modules([str(package_path)]):
        name = module_info.name

        if not name.startswith("embedding_"):
            continue

        module = importlib.import_module(
            f"backend.tasks.ingest.embedding.{name}"
        )

        if hasattr(module, "SUPPORTED_EXTENSIONS"):
            modules.append(module)

    return modules



# -------------------------
# Identifier Resolution
# -------------------------

def resolve_uses(language_chunks: List[Dict]):

    identifier_registry = set()

    for chunk in language_chunks:
        identifier = chunk.get("identifier")
        if identifier:
            identifier_registry.add(identifier)

    for chunk in language_chunks:
        if "uses" in chunk:
            chunk["uses"] = [
                u for u in chunk["uses"]
                if u in identifier_registry
            ]


# -------------------------
# Main Dispatcher Entry
# -------------------------

def process_repository(repo_path: Path, repo_url: str | None = None):

    language_modules = load_language_modules()
    processed_files: Set[Path] = set()

    # -------------------------
    # Per-Language Processing
    # -------------------------

    for module in language_modules:

        language_chunks = []
        supported_extensions = {
            ext.lower() for ext in module.SUPPORTED_EXTENSIONS
        }

        # Phase A: Collect chunks for this language
        IGNORED_DIRS = {
            ".git",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            ".pytest_cache",
            "dist",
            "build"
        }

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            if any(part in IGNORED_DIRS for part in file_path.parts):
                continue


            if file_path.suffix.lower() in supported_extensions:
                chunks = module.extract_chunks(file_path)

                relative_path = file_path.relative_to(repo_path)

                for idx, chunk in enumerate(chunks):
                    chunk["file_path"] = str(relative_path)
                    chunk["chunk_number"] = idx
                    if repo_url:
                        chunk["repo_url"] = repo_url

                language_chunks.extend(chunks)
                processed_files.add(file_path)

        if not language_chunks:
            continue

        # Phase B: Resolve Uses (if implemented)
        if getattr(module, "implements_uses", False):
            resolve_uses(language_chunks)

        # Phase C: Embed + Insert
        for chunk in language_chunks:
            content = chunk.get("content", "").strip()
            if not content:
                continue  # skip empty chunks

            embedding = embed_text(content)

            if not embedding or len(embedding) == 0:
                continue  # skip invalid embeddings

            chunk["embedding"] = embedding
            insert_chunks([chunk])


        # Flush memory
        language_chunks.clear()

    # -------------------------
    # Blind Chunking
    # -------------------------

    IGNORED_DIRS = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".pytest_cache",
        "dist",
        "build"
    }

    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue

        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue


        if file_path in processed_files:
            continue

        chunks = fallback_extract(file_path)

        relative_path = file_path.relative_to(repo_path)

        for idx, chunk in enumerate(chunks):
            chunk["file_path"] = str(relative_path)
            chunk["chunk_number"] = idx
            if repo_url:
                chunk["repo_url"] = repo_url
            content = chunk.get("content", "").strip()
            if not content:
                continue  # skip empty chunks

            embedding = embed_text(content)

            if not embedding or len(embedding) == 0:
                continue  # skip invalid embeddings

            chunk["embedding"] = embedding
            insert_chunks([chunk])
