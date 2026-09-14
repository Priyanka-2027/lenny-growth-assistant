"""Health and readiness endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health", summary="Liveness probe")
async def health():
    """Returns 200 if the process is running."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe — checks DB and model config")
async def ready(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Returns readiness status including DB connectivity and active model.
    Safe to use as a k8s/Docker readiness probe.
    """
    db_ok = False
    db_error = None
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = str(exc)

    return {
        "status": "ready" if db_ok else "degraded",
        "database": "ok" if db_ok else f"error: {db_error}",
        "llm_provider": settings.llm_provider,
        "active_model": settings.active_model_name,
        "environment": settings.app_env,
    }
