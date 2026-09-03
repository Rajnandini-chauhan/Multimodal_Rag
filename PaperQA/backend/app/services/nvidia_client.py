"""Single client factory for the NVIDIA NIM API.

NIM is OpenAI-compatible, so we reuse the openai SDK with a custom base URL.
Everything in the codebase that previously called x.ai now goes through here.
"""

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()

_client: OpenAI | None = None


def get_nvidia_client() -> OpenAI:
    """Lazy-init a single OpenAI-compatible client pointed at NVIDIA NIM."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            timeout=60.0,
        )
    return _client
