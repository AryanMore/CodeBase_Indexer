# schemas/chunk.py
from typing import Optional, List
from pydantic import BaseModel


class Chunk(BaseModel):
    chunk_id: str
    file_path: str

    content: str                 # text/code snippet
    code_type: Optional[str]     # e.g. py:function, py:imports

    start_line: Optional[int]
    end_line: Optional[int]

    symbols: Optional[List[str]]  # function/class names if available
