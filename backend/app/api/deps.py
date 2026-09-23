"""Shared FastAPI dependencies."""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as _get_db


# Re-export the DB dependency so routers only need to import from deps
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session per request."""
    async for session in _get_db():
        yield session


class PaginationParams:
    """Common pagination query parameters."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(default=20, ge=1, le=200, description="Max records to return"),
    ) -> None:
        self.skip = skip
        self.limit = limit


# Convenience type alias
DBSession = AsyncSession
