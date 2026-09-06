from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
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

    # Paper storage
    upload_dir: str = "./storage/papers"
    max_upload_size_mb: int = 25

    # NVIDIA NIM -- single provider for text + vision + embeddings.
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    llm_model: str = "meta/llama-3.2-11b-vision-instruct"
    vision_model: str = "meta/llama-3.2-11b-vision-instruct"
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


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so the environment is parsed only once."""
    return Settings()
