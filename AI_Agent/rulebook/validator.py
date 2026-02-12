import json
from pathlib import Path
from typing import List

from AI_Agent.schemas.chunk import Chunk
from AI_Agent.schemas.intent import Intent


DEFAULT_RULES = [
    {
        "name": "python_same_file_imports",
        "allowed_intents": ["Explain", "Analyze", "Modify", "Refactor", "Debug"],
        "source_code_types": ["py:function", "py:class"],
        "allowed_requested_code_types": ["py:imports", "py:class_header"],
        "scope": "same_file",
        "max_chunks": 3,
    },
    {
        "name": "python_callers_same_file",
        "allowed_intents": ["Analyze", "Modify", "Debug"],
        "source_code_types": ["py:function"],
        "allowed_requested_code_types": ["py:function"],
        "scope": "same_file",
        "max_chunks": 2,
    },
]


class RulebookViolation(Exception):
    pass


class RulebookValidator:
    def __init__(self, rulebook_path: str | None = None):
        self.rules = DEFAULT_RULES
        if not rulebook_path:
            return

        resolved = Path(rulebook_path)
        if resolved.suffix.lower() == ".json" and resolved.exists():
            data = json.loads(resolved.read_text(encoding="utf-8"))
            self.rules = data.get("expansion_rules", DEFAULT_RULES)

    def validate_expansion(
        self,
        intent: Intent,
        source_chunks: List[Chunk],
        requested_code_types: List[str],
        scope: str,
        max_chunks: int,
    ) -> None:
        for rule in self.rules:
            if intent.value not in rule["allowed_intents"]:
                continue

            source_types = {c.code_type for c in source_chunks if c.code_type}
            if source_types and not source_types.intersection(set(rule["source_code_types"])):
                continue

            if not set(requested_code_types).issubset(set(rule["allowed_requested_code_types"])):
                continue

            if scope != rule["scope"]:
                continue

            if max_chunks > rule["max_chunks"]:
                continue

            return

        raise RulebookViolation(
            f"Expansion denied by rulebook: intent={intent}, requested_code_types={requested_code_types}, scope={scope}"
        )
