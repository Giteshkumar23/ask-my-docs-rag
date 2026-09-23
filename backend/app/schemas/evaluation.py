"""Pydantic v2 schemas for Evaluation API requests and responses."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------ #
# Request schemas
# ------------------------------------------------------------------ #

class EvaluationRunRequest(BaseModel):
    """Trigger an evaluation run against a named dataset."""

    name: str = Field(..., min_length=1, max_length=256)
    dataset_name: str = Field(..., min_length=1, max_length=256)


# ------------------------------------------------------------------ #
# Response schemas
# ------------------------------------------------------------------ #

class EvaluationResultResponse(BaseModel):
    """Per-question evaluation result."""

    id: uuid.UUID
    run_id: uuid.UUID
    question: str
    expected_answer: str
    generated_answer: Optional[str] = None
    expected_sources: Optional[Dict[str, Any]] = None
    retrieved_sources: Optional[Dict[str, Any]] = None
    faithfulness_score: Optional[float] = None
    relevance_score: Optional[float] = None
    citation_score: Optional[float] = None
    retrieval_recall: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationRunResponse(BaseModel):
    """Full evaluation run summary."""

    id: uuid.UUID
    name: str
    dataset_name: str
    recall_at_5: Optional[float] = None
    precision_at_5: Optional[float] = None
    mrr: Optional[float] = None
    hit_rate: Optional[float] = None
    faithfulness: Optional[float] = None
    answer_relevance: Optional[float] = None
    context_relevance: Optional[float] = None
    citation_accuracy: Optional[float] = None
    citation_coverage: Optional[float] = None
    avg_retrieval_latency: Optional[float] = None
    avg_reranking_latency: Optional[float] = None
    avg_generation_latency: Optional[float] = None
    avg_total_latency: Optional[float] = None
    num_questions: int = 0
    passed: Optional[bool] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationRunListResponse(BaseModel):
    """Paginated list of evaluation runs."""

    items: List[EvaluationRunResponse]
    total: int
    skip: int
    limit: int
