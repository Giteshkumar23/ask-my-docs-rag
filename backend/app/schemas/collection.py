"""Pydantic v2 schemas for Collection API requests and responses."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------ #
# Request schemas
# ------------------------------------------------------------------ #

class CollectionCreate(BaseModel):
    """Payload for creating a new collection."""

    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=2048)
    color: str = Field(default="#3b82f6", pattern=r"^#[0-9a-fA-F]{6}$")


class CollectionUpdate(BaseModel):
    """Partial update payload for an existing collection."""

    name: Optional[str] = Field(None, min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=2048)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


# ------------------------------------------------------------------ #
# Response schemas
# ------------------------------------------------------------------ #

class CollectionResponse(BaseModel):
    """Full collection representation returned by the API."""

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    color: str
    document_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionListResponse(BaseModel):
    """Paginated list of collections."""

    items: List[CollectionResponse]
    total: int
    skip: int
    limit: int
