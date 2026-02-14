import os

import ollama
from dotenv import load_dotenv

from backend.config import EMBEDDING_MODEL, GROQ_MODEL, LLM_MODEL, USE_GROQ

load_dotenv()

_GROQ_CLIENTS = None
_GROQ_START_INDEX = 0


def embed_text(text: str) -> list:
    response = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=text,
    )
    return response["embedding"]


def _load_groq_clients():
    global _GROQ_CLIENTS

    if _GROQ_CLIENTS is not None:
        return _GROQ_CLIENTS

    keys = [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_PRIMARY"),
        os.getenv("GROQ_API_KEY_SECONDARY"),
    ]
    seen = set()
    deduped = []
    for key in keys:
        if key and key not in seen:
            deduped.append(key)
            seen.add(key)

    if not deduped:
        raise RuntimeError("No Groq API key configured. Set GROQ_API_KEY (or _1/_2).")

    from groq import Groq

    _GROQ_CLIENTS = [Groq(api_key=key) for key in deduped]
    return _GROQ_CLIENTS


def _is_rate_limited_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return True

    msg = str(exc).lower()
    return "rate" in msg and "limit" in msg or "too many requests" in msg or "rpm" in msg


def _chat_with_groq_failover(prompt: str, max_tokens: int) -> str:
    global _GROQ_START_INDEX

    clients = _load_groq_clients()
    errors = []

    for attempt in range(len(clients)):
        idx = (_GROQ_START_INDEX + attempt) % len(clients)
        client = clients[idx]
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            _GROQ_START_INDEX = (idx + 1) % len(clients)
            return response.choices[0].message.content
        except Exception as exc:
            errors.append(exc)
            if _is_rate_limited_error(exc):
                continue
            raise

    raise RuntimeError(f"All Groq keys exhausted/failed: {[str(e) for e in errors]}")


def chat(prompt: str, max_tokens: int = 200) -> str:
    if USE_GROQ:
        return _chat_with_groq_failover(prompt=prompt, max_tokens=max_tokens)

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"num_predict": max_tokens},
    )
    return response["message"]["content"]
