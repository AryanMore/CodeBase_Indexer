import os
import ollama
from dotenv import load_dotenv
from groq import Groq

from backend.config import (
    EMBEDDING_MODEL,
    USE_GROQ,
    GROQ_MODEL,
    LLM_MODEL
)

load_dotenv()

_groq = None


def embed_text(text: str) -> list:
    response = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=text
    )
    return response["embedding"]


def get_groq_client():
    global _groq
    if _groq is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        _groq = Groq(api_key=api_key)
    return _groq


def chat(prompt: str) -> str:
    if USE_GROQ:
        groq_client = get_groq_client()
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        options={
            "num_predict": 200
        }
    )
    return response["message"]["content"]
