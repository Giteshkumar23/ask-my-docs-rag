"""Pydantic v2 schemas for Query API requests and responses."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------ #
# Request schemas
# ------------------------------------------------------------------ #

class QueryRequest(BaseModel):
    """A question submitted by the user."""

    question: str = Field(
        ..., min_length=3, max_length=4096, description="The natural-language question"
    )
    collection_id: Optional[uuid.UUID] = Field(
        None, description="Restrict retrieval to a specific collection"
    )
    top_k: Optional[int] = Field(
        None, ge=1, le=20, description="Override TOP_K_FINAL for this request"
    )


# ------------------------------------------------------------------ #
# Response schemas
# ------------------------------------------------------------------ #

class CitationResponse(BaseModel):
    """A source citation embedded in a generated answer."""

    citation_number: int
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    text_snippet: str = Field(..., description="First 300 chars of the chunk text")
    is_valid: bool = True

    model_config = ConfigDict(from_attributes=True)


class QueryResultDetail(BaseModel):
    """Scoring detail for a single retrieved chunk."""

    chunk_id: uuid.UUID
    rank: int
    bm25_score: Optional[float] = None
    vector_score: Optional[float] = None
    reranker_score: Optional[float] = None
    fusion_score: Optional[float] = None
    used_in_answer: bool = False

    model_config = ConfigDict(from_attributes=True)


class QueryResponse(BaseModel):
    """Full response returned after a query is processed."""

    id: uuid.UUID
    question: str
    answer: Optional[str] = None
    citations: List[CitationResponse] = []
    confidence: Optional[str] = None
    retrieval_time: Optional[float] = None
    reranking_time: Optional[float] = None
    generation_time: Optional[float] = None
    total_time: Optional[float] = None
    num_chunks_retrieved: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueryListResponse(BaseModel):
    """Paginated list of past queries."""

    items: List[QueryResponse]
    total: int
    skip: int
    limit: int
