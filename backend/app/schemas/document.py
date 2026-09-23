"""Pydantic v2 schemas for Document API requests and responses."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


# ------------------------------------------------------------------ #
# Base / shared
# ------------------------------------------------------------------ #

class DocumentBase(BaseModel):
    """Fields shared by create and response schemas."""

    name: str = Field(..., max_length=512, description="Human-readable document name")
    collection_id: Optional[uuid.UUID] = Field(
        None, description="Optional collection to assign the document to"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias=AliasChoices("metadata_", "metadata"),
        serialization_alias="metadata",
        description="Arbitrary key-value metadata",
    )

    model_config = ConfigDict(populate_by_name=True)


# ------------------------------------------------------------------ #
# Request schemas
# ------------------------------------------------------------------ #

class DocumentUpdate(BaseModel):
    """Partial update payload for an existing document."""

    name: Optional[str] = Field(None, max_length=512)
    collection_id: Optional[uuid.UUID] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")

    model_config = ConfigDict(populate_by_name=True)


# ------------------------------------------------------------------ #
# Response schemas
# ------------------------------------------------------------------ #

class DocumentResponse(DocumentBase):
    """Full document representation returned by the API."""

    id: uuid.UUID
    original_filename: str
    file_type: str
    file_size: int
    num_pages: Optional[int] = None
    num_chunks: int = 0
    status: str
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class DocumentStatusResponse(BaseModel):
    """Lightweight status-only response for polling."""

    id: uuid.UUID
    status: str
    num_chunks: int = 0
    processing_time: Optional[float] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChunkResponse(BaseModel):
    """A single chunk returned to the client (embedding omitted)."""

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    token_count: int
    metadata_: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias=AliasChoices("metadata_", "metadata"),
        serialization_alias="metadata",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
