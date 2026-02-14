import os

EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2:3b"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"
GROQ_MODEL = "llama-3.1-8b-instant"


