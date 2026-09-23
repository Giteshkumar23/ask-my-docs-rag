"""Health check endpoint."""
from __future__ import annotations

from typing import Dict

import structlog
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal

log = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=Dict[str, str], summary="Health check")
async def health_check() -> Dict[str, str]:
    """Return the operational status of the API and its dependencies.

    Returns
    -------
    dict
        ``status`` — overall health (``ok`` / ``error``).
        ``database`` — database reachability (``ok`` / ``error``).
        ``version`` — current application version.
    """
    db_status = "ok"
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        log.error("health.db_error", exc_info=exc)
        db_status = "error"

    overall = "ok" if db_status == "ok" else "error"
    return {
        "status": overall,
        "database": db_status,
        "version": settings.APP_VERSION,
    }
