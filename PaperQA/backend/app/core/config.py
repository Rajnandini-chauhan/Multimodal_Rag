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


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so the environment is parsed only once."""
    return Settings()