import json
import logging
import re
import time
from pathlib import Path

import ollama

MODEL = "llama3.2:3b"

logger = logging.getLogger("ai_agent.llm")


def render_prompt(template_path: str, values: dict[str, str]) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    prompt = template
    for key, value in values.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)
    return prompt


def chat(prompt: str, max_tokens: int = 150) -> str:
    """
    Thin wrapper around ollama.chat that adds structured, timestamped logging so
    we can see how long each LLM call takes and with which model it was made.
    """
    start = time.time()
    logger.info(
        "llm_request_start model=%s max_tokens=%d prompt_preview=%r",
        MODEL,
        max_tokens,
        prompt[:80].replace("\n", " "),
    )
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": max_tokens},
        )
    except Exception as exc:
        elapsed = time.time() - start
        logger.exception(
            "llm_request_error model=%s duration_seconds=%.3f error=%s",
            MODEL,
            elapsed,
            exc,
        )
        raise

    elapsed = time.time() - start
    logger.info(
        "llm_request_end model=%s duration_seconds=%.3f", MODEL, elapsed
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
