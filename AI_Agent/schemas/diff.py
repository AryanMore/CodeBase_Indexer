# schemas/diff.py
from typing import List
from pydantic import BaseModel


class FileDiff(BaseModel):
    file_path: str
    diff: str   # unified diff text


class DiffBundle(BaseModel):
    bundle_id: str
    goal: str

    files: List[FileDiff]
    explanation: str
