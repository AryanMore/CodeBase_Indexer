import subprocess
import tempfile
import uuid
from pathlib import Path

from AI_Agent.repo_registry import get_repo_path
from AI_Agent.schemas.diff import DiffBundle, FileDiff


class GitClient:
    """
    Git + patch operations.

    This client intentionally generates and applies *real git-format patches*
    so downstream `git apply` works without malformed headers like `a/None`.
    """

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self._bundles: dict[str, DiffBundle] = {}

    def _run(self, args: list[str]) -> str:
        result = subprocess.run(
            args,
            cwd=self.repo_root,
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout

    def store_bundle(self, bundle: DiffBundle) -> None:
        self._bundles[bundle.bundle_id] = bundle

    def propose_changes(
        self,
        goal: str,
        affected_files: list[str],
    ) -> DiffBundle:
        diff_cmd = ["git", "diff", "--binary", "--"]
        diff_cmd.extend(affected_files or ["."])
        patch = self._run(diff_cmd)

        bundle = DiffBundle(
            bundle_id=str(uuid.uuid4()),
            goal=goal,
            files=[
                FileDiff(
                    file_path=",".join(affected_files) if affected_files else "WORKTREE",
                    diff=patch,
                )
            ],
            explanation="Patch captured from git worktree in canonical format.",
        )
        self._bundles[bundle.bundle_id] = bundle
        return bundle

    def apply_changes(self, diff_bundle_id: str) -> None:
        bundle = self._bundles.get(diff_bundle_id)
        if not bundle:
            raise RuntimeError(f"Unknown diff bundle id: {diff_bundle_id}")

        patch_text = "\n\n".join(file_diff.diff for file_diff in bundle.files if file_diff.diff)
        if not patch_text.strip():
            return

        with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as tmp:
            tmp.write(patch_text)
            tmp_path = Path(tmp.name)

        try:
            self._run(["git", "apply", "--index", str(tmp_path)])
        finally:
            tmp_path.unlink(missing_ok=True)

    def apply_bundle(self, bundle: DiffBundle) -> None:
        """
        Apply the given diff bundle directly to the current repo_root.

        This bypasses the internal in-memory bundle store and is intended
        for use with bundles loaded from external storage (e.g. AgentMemory).
        """
        patch_text = "\n\n".join(file_diff.diff for file_diff in bundle.files if file_diff.diff)
        if not patch_text.strip():
            return

        with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as tmp:
            tmp.write(patch_text)
            tmp_path = Path(tmp.name)

        try:
            self._run(["git", "apply", "--index", str(tmp_path)])
        finally:
            tmp_path.unlink(missing_ok=True)

    def commit_and_push(self, message: str) -> str:
        self._run(["git", "commit", "-m", message])
        branch = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
        self._run(["git", "push", "origin", branch])
        return branch

    def git_diff(self) -> str:
        return self._run(["git", "diff", "--binary"])

    def export_commit_patch(self, commit_ref: str, output_path: str) -> str:
        patch = self._run(["git", "show", "--format=email", commit_ref])
        out = self.repo_root / output_path
        out.write_text(patch, encoding="utf-8")
        return str(out)


def resolve_repo_root_for_url(repo_url: str) -> Path:
    """
    Resolve the local git worktree for the given repo URL.

    The ingest pipeline records the checkout location in a shared
    repo registry. This helper translates the URL into a concrete
    filesystem path, or raises if the repo has not been ingested.
    """
    repo_path = get_repo_path(repo_url)
    if not repo_path:
        raise RuntimeError(
            f"No local checkout found for repo_url={repo_url!r}. "
            "Make sure you have ingested this repository before approving changes."
        )
    if not repo_path.exists():
        raise RuntimeError(
            f"Registered checkout path does not exist on disk: {repo_path}. "
            "The repository may have been moved or deleted."
        )
    return repo_path
