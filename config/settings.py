"""
config/settings.py

Central place for configuration: API keys, model names,
thresholds, and limits used across the system.

Loads configuration from a local .env file or environment variables.
"""

import os
from dotenv import load_dotenv

from config.paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")


def _get_secret(key: str) -> str | None:
    return os.getenv(key)


def _resolve_model_name() -> str:
    preferred = [
        os.getenv("MODEL_NAME"),
        "openai/gpt-oss-20b",
        "qwen/qwen3.6-27b",
        "llama-3.3-70b-versatile",
        "groq/compound-mini",
    ]
    preferred = [m for m in preferred if m]

    if not GROQ_API_KEY:
        return preferred[0] if preferred else "openai/gpt-oss-20b"

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        available = {model.id for model in client.models.list().data}
        for candidate in preferred:
            if candidate in available:
                return candidate
        return preferred[0] if preferred else "openai/gpt-oss-20b"
    except Exception:
        return preferred[0] if preferred else "openai/gpt-oss-20b"


GROQ_API_KEY = _get_secret("GROQ_API_KEY")
MODEL_NAME = _resolve_model_name()

CRISIS_CONFIDENCE_THRESHOLD = 0.5

MAX_SUPERVISOR_TURNS = 10

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Add it to .env as "
        "GROQ_API_KEY=your_key_here or set it as an environment variable."
    )