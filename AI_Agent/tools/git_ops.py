# tools/git_ops.py
from typing import Optional
from schemas.diff import DiffBundle


class GitClient:
    """
    Git + patch operations.
    """

    def propose_changes(
        self,
        goal: str,
        affected_files: list[str],
    ) -> DiffBundle:
        """
        Generates a diff bundle.
        Does NOT write files.
        """
        raise NotImplementedError("Git.propose_changes not implemented")

    def apply_changes(self, diff_bundle_id: str) -> None:
        """
        Applies an approved diff bundle.
        Must fail closed if approval is missing.
        """
        raise NotImplementedError("Git.apply_changes not implemented")

    def git_diff(self) -> str:
        """
        Shows pending changes.
        """
        raise NotImplementedError("Git.git_diff not implemented")
