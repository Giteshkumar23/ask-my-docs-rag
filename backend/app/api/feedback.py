"""Feedback API router — full implementation."""
from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_db
from app.models.feedback import Feedback
from app.models.query import Query as QueryModel
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackResponse,
)

router = APIRouter(prefix="/feedback")
log = structlog.get_logger(__name__)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=FeedbackResponse,
    summary="Submit feedback",
)
async def submit_feedback(
    body: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Submit a rating for a completed query."""
    # Verify query exists
    q_result = await db.execute(
        select(QueryModel).where(QueryModel.id == body.query_id)
    )
    if q_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Query not found")

    fb = Feedback(
        id=uuid.uuid4(),
        query_id=body.query_id,
        rating=body.rating,
        comment=body.comment,
        failure_category=body.failure_category,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    log.info("feedback.submitted", feedback_id=str(fb.id), rating=fb.rating)
    return FeedbackResponse.model_validate(fb)


@router.get(
    "",
    response_model=FeedbackListResponse,
    summary="List feedback",
)
async def list_feedback(
    pagination: PaginationParams = Depends(),
    rating: Optional[str] = Query(None, pattern="^(positive|negative)$"),
    db: AsyncSession = Depends(get_db),
) -> FeedbackListResponse:
    """Return paginated feedback records, optionally filtered by rating."""
    base = select(Feedback)
    count_q = select(func.count()).select_from(Feedback)
    if rating is not None:
        base = base.where(Feedback.rating == rating)
        count_q = count_q.where(Feedback.rating == rating)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        base.order_by(Feedback.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    items = list(result.scalars().all())
    return FeedbackListResponse(
        items=[FeedbackResponse.model_validate(f) for f in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/summary",
    summary="Feedback summary",
)
async def get_feedback_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """Return aggregate feedback statistics."""
    result = await db.execute(
        select(Feedback.rating, func.count().label("cnt")).group_by(Feedback.rating)
    )
    counts = {row.rating: row.cnt for row in result.all()}
    positive = counts.get("positive", 0)
    negative = counts.get("negative", 0)
    total = positive + negative
    return {
        "positive": positive,
        "negative": negative,
        "total": total,
        "positive_rate": (positive / total) if total > 0 else None,
    }


@router.get(
    "/{feedback_id}",
    response_model=FeedbackResponse,
    summary="Get feedback",
)
async def get_feedback(
    feedback_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Return a single feedback record."""
    result = await db.execute(
        select(Feedback).where(Feedback.id == feedback_id)
    )
    fb = result.scalar_one_or_none()
    if fb is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return FeedbackResponse.model_validate(fb)
