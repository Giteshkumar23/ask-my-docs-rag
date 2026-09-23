"""Evaluation API router — full implementation."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_db
from app.models.evaluation import EvaluationResult, EvaluationRun
from app.schemas.evaluation import (
    EvaluationResultResponse,
    EvaluationRunListResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
)

router = APIRouter(prefix="/evaluation")
log = structlog.get_logger(__name__)


# --------------------------------------------------------------------------- #
# Background task
# --------------------------------------------------------------------------- #


async def _run_evaluation_bg(run_id: uuid.UUID, dataset: List[Dict[str, Any]]) -> None:
    """Run evaluation in background with its own DB session."""
    from app.core.database import SessionLocal  # noqa: PLC0415
    from app.evaluation.runner import EvaluationRunner  # noqa: PLC0415

    async with SessionLocal() as db:
        try:
            runner = EvaluationRunner(db=db)
            await runner.run_evaluation(run_id=run_id, dataset=dataset)
        except Exception:
            log.exception("evaluation.bg.failed", run_id=str(run_id))


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


@router.post(
    "/runs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EvaluationRunResponse,
    summary="Start evaluation run",
)
async def start_evaluation_run(
    body: EvaluationRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> EvaluationRunResponse:
    """Create an evaluation run record and trigger async evaluation."""
    run = EvaluationRun(
        id=uuid.uuid4(),
        name=body.name,
        dataset_name=body.dataset_name,
        num_questions=0,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Launch background evaluation (dataset is empty for now; runner will load by name)
    background_tasks.add_task(_run_evaluation_bg, run.id, [])
    log.info("evaluation.run.created", run_id=str(run.id), name=body.name)
    return EvaluationRunResponse.model_validate(run)


@router.get(
    "/runs",
    response_model=EvaluationRunListResponse,
    summary="List evaluation runs",
)
async def list_evaluation_runs(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> EvaluationRunListResponse:
    """Return paginated evaluation runs."""
    total = (await db.execute(select(func.count()).select_from(EvaluationRun))).scalar_one()
    result = await db.execute(
        select(EvaluationRun)
        .order_by(EvaluationRun.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    items = list(result.scalars().all())
    return EvaluationRunListResponse(
        items=[EvaluationRunResponse.model_validate(r) for r in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/runs/{run_id}",
    response_model=EvaluationRunResponse,
    summary="Get evaluation run",
)
async def get_evaluation_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> EvaluationRunResponse:
    """Return a single evaluation run with aggregated metrics."""
    result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return EvaluationRunResponse.model_validate(run)


@router.get(
    "/runs/{run_id}/results",
    summary="Get per-question results",
)
async def get_evaluation_results(
    run_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return paginated per-question results for a run."""
    run_result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )
    if run_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found")

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
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    items = list(result.scalars().all())

    return {
        "items": [EvaluationResultResponse.model_validate(r) for r in items],
        "total": total,
        "skip": pagination.skip,
        "limit": pagination.limit,
    }
