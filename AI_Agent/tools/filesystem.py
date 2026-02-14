from pathlib import Path
from typing import List

from AI_Agent.schemas.chunk import Chunk


class FileSystemClient:
    def get_file_chunks(self, file_path: str) -> List[Chunk]:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return []

        content = path.read_text(encoding="utf-8", errors="ignore")
        return [
            Chunk(
                chunk_id=f"local:{file_path}",
                file_path=file_path,
                content=content,
                code_type=None,
                start_line=1,
                end_line=len(content.splitlines()),
                symbols=None,
            )
        ]
