import json
import re
from pathlib import Path

import ollama

MODEL = "llama3.2:3b"


def render_prompt(template_path: str, values: dict[str, str]) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    prompt = template
    for key, value in values.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)
    return prompt


def chat(prompt: str, max_tokens: int = 300) -> str:
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
