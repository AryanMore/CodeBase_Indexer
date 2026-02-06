import subprocess
from pathlib import Path
import uuid

def clone_repo(repo_url: str) -> Path:
    base_tmp_dir = Path(__file__).resolve().parents[1] / "tmp"
    base_tmp_dir.mkdir(parents=True, exist_ok=True)

    repo_dir = base_tmp_dir / f"repo_{uuid.uuid4().hex}"
    print("Cloning repo:", repo_url)
    command = [
        "git",
        "clone",
        repo_url,
        str(repo_dir)
    ]


    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Git clone failed: {result.stderr}")
    print("Git stdout:", result.stdout)
    print("Git stderr:", result.stderr)

    return repo_dir
