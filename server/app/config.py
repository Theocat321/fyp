import os
from typing import Optional
from pathlib import Path

try:
    # Load root .env so both apps share a single file in dev
    from dotenv import load_dotenv  # type: ignore

    _root = Path(__file__).resolve().parents[2]
    load_dotenv(_root / ".env", override=False)
except Exception:
    # If python-dotenv isn't installed or file missing, continue gracefully
    pass


def get_provider_name() -> str:
    return os.getenv("PROVIDER_NAME", "VodaCare")


def get_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


def get_openai_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY") or None


def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_openai_base_url() -> Optional[str]:
    return os.getenv("OPENAI_BASE_URL") or None


def get_assistant_mode() -> str:
    """Assistant mode: 'open' (default) or 'strict'."""
    v = (os.getenv("ASSISTANT_MODE", "open") or "").lower()
    return "strict" if v == "strict" else "open"
