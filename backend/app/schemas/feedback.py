"""Pydantic v2 schemas for the Feedback API."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------ #
# Request schemas
# ------------------------------------------------------------------ #

class FeedbackCreate(BaseModel):
    """Submit feedback for a completed query."""

    query_id: uuid.UUID
    rating: str = Field(..., pattern=r"^(positive|negative)$")
    comment: Optional[str] = Field(None, max_length=2048)
    failure_category: Optional[str] = Field(
        None,
        max_length=64,
        description=(
            "One of: wrong_answer | missing_citation | hallucination | "
            "irrelevant | incomplete | other"
        ),
    )


# ------------------------------------------------------------------ #
# Response schemas
# ------------------------------------------------------------------ #

class FeedbackResponse(BaseModel):
    """Feedback record returned by the API."""

    id: uuid.UUID
    query_id: uuid.UUID
    rating: str
    comment: Optional[str] = None
    failure_category: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackListResponse(BaseModel):
    """Paginated list of feedback records."""

    items: List[FeedbackResponse]
    total: int
    skip: int
    limit: int
