import os


def get_provider_name() -> str:
    return os.getenv("PROVIDER_NAME", "VodaCare")


def get_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


def get_openai_api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY") or None


def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_openai_base_url() -> str | None:
    return os.getenv("OPENAI_BASE_URL") or None
