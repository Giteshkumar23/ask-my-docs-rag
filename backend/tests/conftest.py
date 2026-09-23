"""Shared pytest fixtures for the Ask My Docs test suite.

Provides:
- ``app``        — the FastAPI application instance
- ``async_client`` — an httpx AsyncClient wired to the test app
- ``db_session``  — an async SQLAlchemy session against an in-memory SQLite DB

SQLite is used for unit / integration tests so the suite can run without a
running PostgreSQL instance.  pgvector-specific columns are excluded from
SQLite tests (the Vector column type requires PostgreSQL); models that use it
are patched accordingly via a separate fixture.
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.main import app
from app.api.deps import get_db

# --------------------------------------------------------------------------- #
# Event loop
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# --------------------------------------------------------------------------- #
# In-memory SQLite engine (unit / integration tests)
# --------------------------------------------------------------------------- #

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a session-scoped in-memory SQLite engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        # Skip Vector columns which are PostgreSQL-only
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional AsyncSession that is rolled back after each test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# --------------------------------------------------------------------------- #
# Test HTTP client
# --------------------------------------------------------------------------- #

@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an httpx AsyncClient pointed at the FastAPI test app.

    The ``get_db`` dependency is overridden to use the test session so all
    requests share the same rolled-back transaction.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()
