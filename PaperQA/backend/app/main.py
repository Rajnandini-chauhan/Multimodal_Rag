from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import auth, papers
from app.core.config import get_settings
from app.database.session import engine

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(papers.router)

# ... /health endpoint stays exactly as before ...
@app.get("/health")
def health() -> dict:
    """Liveness + readiness check. Confirms the API is running, settings are
    loaded, and the database connection is actually reachable."""
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok",
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "database": db_status,
    }