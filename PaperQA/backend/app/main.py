from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> dict:
    """Basic liveness check. Confirms the API is running and reports current settings."""
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "app_env": settings.app_env,
    }