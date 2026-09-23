"""Analytics service — full implementation.

Aggregation helpers used by the analytics API router.
All heavy queries live in the router itself; this module provides
reusable helpers for potential Celery tasks or scheduled reports.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.feedback import Feedback
from app.models.query import Query
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    ConfidenceBreakdown,
    DailyQueryCount,
    FeedbackSummary,
    LatencyStats,
)

log = structlog.get_logger(__name__)


class AnalyticsService:
    """Aggregates usage metrics for the analytics dashboard."""

    @staticmethod
    async def get_summary(db: AsyncSession) -> AnalyticsSummaryResponse:
        """Return a full analytics summary payload."""
        total_docs = (await db.execute(select(func.count()).select_from(Document))).scalar_one()
        total_chunks = (await db.execute(select(func.count()).select_from(DocumentChunk))).scalar_one()
        total_queries = (await db.execute(select(func.count()).select_from(Query))).scalar_one()

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        daily_result = await db.execute(
            select(
                func.date(Query.created_at).label("day"),
                func.count().label("cnt"),
            )
            .where(Query.created_at >= thirty_days_ago)
            .group_by(func.date(Query.created_at))
            .order_by(func.date(Query.created_at))
        )
        daily_queries = [
            DailyQueryCount(date=row.day, count=row.cnt)
            for row in daily_result.all()
        ]

        conf_result = await db.execute(
            select(Query.confidence, func.count().label("cnt"))
            .where(Query.confidence.isnot(None))
            .group_by(Query.confidence)
        )
        conf_map: Dict[str, int] = {row.confidence: row.cnt for row in conf_result.all()}
        confidence_breakdown = ConfidenceBreakdown(
            high=conf_map.get("high", 0),
            moderate=conf_map.get("moderate", 0),
            low=conf_map.get("low", 0),
            insufficient=conf_map.get("insufficient", 0),
        )

        lat_result = await db.execute(
            select(
                func.avg(Query.retrieval_time).label("avg_ret"),
                func.avg(Query.reranking_time).label("avg_rank"),
                func.avg(Query.generation_time).label("avg_gen"),
                func.avg(Query.total_time).label("avg_total"),
            ).where(Query.status == "completed")
        )
        lat_row = lat_result.one()

        try:
            p95_result = await db.execute(
                text(
                    "SELECT percentile_cont(0.95) WITHIN GROUP "
                    "(ORDER BY total_time) AS p95 FROM queries WHERE status='completed'"
                )
            )
            p95 = p95_result.scalar_one()
        except Exception:
            p95 = None

        latency_stats = LatencyStats(
            avg_retrieval=lat_row.avg_ret,
            avg_reranking=lat_row.avg_rank,
            avg_generation=lat_row.avg_gen,
            avg_total=lat_row.avg_total,
            p95_total=p95,
        )

        fb_result = await db.execute(
            select(Feedback.rating, func.count().label("cnt")).group_by(Feedback.rating)
        )
        fb_map: Dict[str, int] = {row.rating: row.cnt for row in fb_result.all()}
        positive = fb_map.get("positive", 0)
        negative = fb_map.get("negative", 0)
        total_fb = positive + negative
        feedback_summary = FeedbackSummary(
            positive=positive,
            negative=negative,
            total=total_fb,
            positive_rate=(positive / total_fb) if total_fb > 0 else None,
        )

        fail_result = await db.execute(
            select(Feedback.failure_category, func.count().label("cnt"))
            .where(Feedback.rating == "negative")
            .where(Feedback.failure_category.isnot(None))
            .group_by(Feedback.failure_category)
            .order_by(func.count().desc())
            .limit(10)
        )
        top_failure_categories: Dict[str, int] = {
            row.failure_category: row.cnt for row in fail_result.all()
        }

        return AnalyticsSummaryResponse(
            total_queries=total_queries,
            total_documents=total_docs,
            total_chunks=total_chunks,
            daily_queries=daily_queries,
            confidence_breakdown=confidence_breakdown,
            latency_stats=latency_stats,
            feedback_summary=feedback_summary,
            top_failure_categories=top_failure_categories,
        )
