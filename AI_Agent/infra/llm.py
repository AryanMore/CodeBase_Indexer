import json
import os
import re
import logging
import re
import time
from pathlib import Path

import ollama

MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

_GROQ_CLIENTS = None
_GROQ_START_INDEX = 0
MODEL = "llama3.2:3b"

logger = logging.getLogger("ai_agent.llm")


def render_prompt(template_path: str, values: dict[str, str]) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    prompt = template
    for key, value in values.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)
    return prompt


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


def chat(prompt: str, max_tokens: int = 300) -> str:
    if USE_GROQ:
        return _chat_with_groq_failover(prompt=prompt, max_tokens=max_tokens)

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0, "num_predict": max_tokens},
    )
    return response["message"]["content"]


def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))
