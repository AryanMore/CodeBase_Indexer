# tools/filesystem.py
from typing import List
from schemas.chunk import Chunk


class FileSystemClient:
    """
    Loads full file context in structured (chunked) form.
    """

    def get_file_chunks(self, file_path: str) -> List[Chunk]:
        """
        Returns the full file as structured chunks.
        Never returns raw text.
        """
        raise NotImplementedError("FS.get_file_chunks not implemented")
