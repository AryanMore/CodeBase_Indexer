# schemas/intent.py
from enum import Enum


class Intent(str, Enum):
    LOCATE = "Locate"
    EXPLAIN = "Explain"
    ANALYZE = "Analyze"
    MODIFY = "Modify"
    REFACTOR = "Refactor"
    DEBUG = "Debug"
