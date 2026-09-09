"""Central configuration for the resume-filtering pipeline.

Reads settings from environment variables / .env located at the project root,
so it works regardless of the current working directory (Streamlit, pytest, CLI).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Always load .env from the project root, not the current working directory.
load_dotenv(PROJECT_ROOT / ".env")


def get_groq_api_key() -> str | None:
    """Return the Groq API key from the environment (or .env)."""
    key = os.getenv("GROQ_API_KEY")
    return key.strip() if key else None


def get_groq_model() -> str:
    """Groq chat model used for structured extraction."""
    return os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()


def get_embedding_model_name() -> str:
    return os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2").strip()


# --- Matching thresholds (tunable via env without touching code) ---

def get_fuzzy_threshold() -> float:
    return float(os.getenv("FUZZY_THRESHOLD", "0.85"))


def get_fuzzy_partial_threshold() -> float:
    return float(os.getenv("FUZZY_PARTIAL_THRESHOLD", "0.70"))


def get_semantic_match_threshold() -> float:
    return float(os.getenv("SEMANTIC_MATCH_THRESHOLD", "0.75"))


def get_semantic_partial_threshold() -> float:
    return float(os.getenv("SEMANTIC_PARTIAL_THRESHOLD", "0.55"))
