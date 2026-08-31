"""LLM provider interface supporting Groq with fallback handling."""

import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> dict:
    """Execute LLM prompt against Groq provider."""
    groq_key = os.environ.get("GROQ_API_KEY")

    if groq_key:
        try:
            return _call_groq(system_prompt, user_prompt, max_tokens, groq_key)
        except Exception as e:
            return {
                "text": None,
                "mode": "mock",
                "provider": None,
                "error": f"Groq: {type(e).__name__}: {e}",
            }

    return {"text": None, "mode": "mock", "provider": None, "error": "no GROQ_API_KEY set"}


def _call_groq(system_prompt, user_prompt, max_tokens, api_key):
    # pyrefly: ignore [missing-import]
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_completion_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = response.choices[0].message.content
    return {"text": text.strip(), "mode": "live", "provider": f"groq:{GROQ_MODEL}"}

