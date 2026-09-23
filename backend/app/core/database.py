"""Async SQLAlchemy engine, session factory, and helpers.

Usage
-----
    from app.core.database import get_db, init_db

    # In FastAPI startup:
    await init_db()
    await create_vector_extension()

    # In route handlers (via dependency injection):
    async def route(db: AsyncSession = Depends(get_db)): ...
"""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _build_engine() -> AsyncEngine:
    """Create the async SQLAlchemy engine from *settings.DATABASE_URL*."""
    return create_async_engine(
        settings.DATABASE_URL,
        echo=False,          # set True to log SQL in development
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # reconnect on stale connections
        pool_recycle=3600,
    )


engine: AsyncEngine = _build_engine()

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an :class:`AsyncSession` per request.

    The session is always closed in the ``finally`` block, even when the
    handler raises an exception.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables defined in the ORM models.

    This is called once on application startup.  In production you should
    rely on Alembic migrations instead; this function is kept for development
    convenience and integration tests.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified.")


async def create_vector_extension() -> None:
    """Enable the ``pgvector`` extension inside PostgreSQL.

    Safe to call multiple times — uses ``CREATE EXTENSION IF NOT EXISTS``.
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    logger.info("pgvector extension enabled.")
