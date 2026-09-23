"""Pydantic v2 schemas for the Analytics API."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DailyQueryCount(BaseModel):
    """Number of queries on a given date."""

    date: date
    count: int


class ConfidenceBreakdown(BaseModel):
    """Count of queries per confidence level."""

    high: int = 0
    moderate: int = 0
    low: int = 0
    insufficient: int = 0


class LatencyStats(BaseModel):
    """Summary latency statistics (seconds)."""

    avg_retrieval: Optional[float] = None
    avg_reranking: Optional[float] = None
    avg_generation: Optional[float] = None
    avg_total: Optional[float] = None
    p95_total: Optional[float] = None


class FeedbackSummary(BaseModel):
    """Aggregate feedback counts."""

    positive: int = 0
    negative: int = 0
    total: int = 0
    positive_rate: Optional[float] = Field(
        None, description="Positive / total, in [0, 1]"
    )


class AnalyticsSummaryResponse(BaseModel):
    """Top-level analytics dashboard payload."""

    total_queries: int
    total_documents: int
    total_chunks: int
    daily_queries: List[DailyQueryCount]
    confidence_breakdown: ConfidenceBreakdown
    latency_stats: LatencyStats
    feedback_summary: FeedbackSummary
    top_failure_categories: Dict[str, int] = Field(
        default_factory=dict,
        description="failure_category → count for negative feedback",
    )
