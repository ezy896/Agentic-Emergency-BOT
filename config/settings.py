"""
config/settings.py

Central place for configuration: API keys, model names,
thresholds, and limits used across the system.

Works both locally (.env file) and on Streamlit Community
Cloud (st.secrets) without code changes.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str) -> str | None:
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)


GROQ_API_KEY = _get_secret("GROQ_API_KEY")

MODEL_NAME = "llama-3.3-70b-versatile"  # solid, fast, good instruction-following

CRISIS_CONFIDENCE_THRESHOLD = 0.8

MAX_SUPERVISOR_TURNS = 10

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Locally: add it to .env as "
        "GROQ_API_KEY=your_key_here. On Streamlit Cloud: add it "
        "under App Settings → Secrets."
    )