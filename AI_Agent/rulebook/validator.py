# rulebook/validator.py
import yaml
from typing import List
from schemas.chunk import Chunk
from schemas.intent import Intent


class RulebookViolation(Exception):
    pass


class RulebookValidator:
    def __init__(self, rulebook_path: str = "rulebook/rules.yaml"):
        with open(rulebook_path, "r") as f:
            self.rules = yaml.safe_load(f)["expansion_rules"]

    def validate_expansion(
        self,
        intent: Intent,
        source_chunks: List[Chunk],
        requested_code_types: List[str],
        scope: str,
        max_chunks: int,
    ) -> None:
        """
        Raises RulebookViolation if expansion is not allowed.
        """

        for rule in self.rules:
            if intent.value not in rule["allowed_intents"]:
                continue

            source_types = {
                c.code_type for c in source_chunks if c.code_type
            }

            if not source_types.intersection(set(rule["source_code_types"])):
                continue

            if not set(requested_code_types).issubset(
                set(rule["allowed_requested_code_types"])
            ):
                continue

            if scope != rule["scope"]:
                continue

            if max_chunks > rule["max_chunks"]:
                continue

            # ✅ Rule matched → expansion allowed
            return

        # ❌ No rule matched
        raise RulebookViolation(
            f"Expansion denied by rulebook: "
            f"intent={intent}, "
            f"requested_code_types={requested_code_types}, "
            f"scope={scope}"
        )
