# schemas/plan.py
from typing import List, Optional
from pydantic import BaseModel


class Plan(BaseModel):
    intent: str

    steps: List[str]

    requires_expansion: bool = False
    requires_full_file: bool = False

    target_files: Optional[List[str]] = None
