from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=(_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "PaperQA"
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+psycopg://paperqa:paperqa@localhost:5432/paperqa"

    # Auth
    jwt_secret_key: str = "replace-with-a-secure-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    google_client_id: str = ""

    # Paper storage
    upload_dir: str = "./storage/papers"
    max_upload_size_mb: int = 25

    # NVIDIA NIM -- single provider for text + vision + embeddings.
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    llm_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    vision_model: str = "nvidia/nemotron-3.5-super-vl-120b-a12b"
    # NV-EmbedQA-E5-v5 is NVIDIA's free retrieval-optimized asymmetric embedding
    # model (passage vs query) currently available on NIM. Replaces the older
    # nvidia/nv-embed-qa, which was retired and now 404s, and meta/muse-glimmer-30b,
    # which was a multimodal generation model that never worked on /v1/embeddings.
    embedding_model: str = "nvidia/nv-embedqa-e5-v5"
    embedding_dim: int = 1024
    embedding_input: str = "passage"

    chroma_persist_dir: str = "./storage/chroma"

    # Async task queue
    redis_url: str = "redis://localhost:6379/0"

    # How long an IngestionJob can sit in PENDING before we treat it as
    # orphaned and allow re-queuing. Without this, a worker that died
    # mid-startup would leave jobs stuck forever (see README troubleshooting).
    stale_job_after_seconds: int = 300

    @field_validator("upload_dir", "chroma_persist_dir", mode="after")
    @classmethod
    def _resolve_relative_paths(cls, v: str) -> str:
        p = Path(v)
        if not p.is_absolute():
            return str((_BACKEND_DIR / p).resolve())
        return str(p)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so the environment is parsed only once."""
    return Settings()
