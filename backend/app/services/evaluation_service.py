"""Evaluation service — full implementation.

Thin wrapper around the EvaluationRunner and DB queries used by the
evaluation API router.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationResult, EvaluationRun

log = structlog.get_logger(__name__)


class EvaluationService:
    """Provides CRUD operations for EvaluationRun records."""

    @staticmethod
    async def get_run(db: AsyncSession, run_id: uuid.UUID) -> Optional[EvaluationRun]:
        """Return an evaluation run by ID."""
        result = await db.execute(
            select(EvaluationRun).where(EvaluationRun.id == run_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_runs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[EvaluationRun], int]:
        """Return paginated evaluation runs and total count."""
        total = (
            await db.execute(select(func.count()).select_from(EvaluationRun))
        ).scalar_one()
        result = await db.execute(
            select(EvaluationRun)
            .order_by(EvaluationRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_results(
        db: AsyncSession,
        run_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[EvaluationResult], int]:
        """Return per-question results for a given run."""
        total = (
            await db.execute(
                select(func.count())
                .select_from(EvaluationResult)
                .where(EvaluationResult.run_id == run_id)
            )
        ).scalar_one()
        result = await db.execute(
            select(EvaluationResult)
            .where(EvaluationResult.run_id == run_id)
            .order_by(EvaluationResult.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total
