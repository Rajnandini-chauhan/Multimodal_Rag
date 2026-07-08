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

    # AI / RAG
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    gemini_api_key: str = ""
    llm_model: str = "gemini-2.0-flash"
    chroma_persist_dir: str = "./storage/chroma"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so the environment is parsed only once."""
    return Settings()