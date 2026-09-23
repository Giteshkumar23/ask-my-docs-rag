"""SQLAlchemy ORM models for RAG queries, results, and citations."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Query(Base):
    """A user question submitted to the RAG pipeline."""

    __tablename__ = "queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    retrieval_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reranking_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generation_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    num_chunks_retrieved: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True
    )  # high | moderate | low | insufficient
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True
    )  # pending | processing | completed | failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    results: Mapped[list["QueryResult"]] = relationship(
        "QueryResult", back_populates="query", cascade="all, delete-orphan"
    )
    citations: Mapped[list["Citation"]] = relationship(
        "Citation", back_populates="query", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["Feedback"]] = relationship(  # noqa: F821
        "Feedback", back_populates="query", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Query id={self.id!s} status={self.status!r} "
            f"confidence={self.confidence!r}>"
        )


class QueryResult(Base):
    """A single chunk retrieved and ranked for a :class:`Query`."""

    __tablename__ = "query_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    bm25_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vector_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reranker_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fusion_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    used_in_answer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    query: Mapped["Query"] = relationship("Query", back_populates="results")

    def __repr__(self) -> str:
        return (
            f"<QueryResult id={self.id!s} query={self.query_id!s} "
            f"rank={self.rank} fusion={self.fusion_score}>"
        )


class Citation(Base):
    """A source citation extracted from a generated answer."""

    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citation_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    query: Mapped["Query"] = relationship("Query", back_populates="citations")

    def __repr__(self) -> str:
        return (
            f"<Citation id={self.id!s} query={self.query_id!s} "
            f"num={self.citation_number} valid={self.is_valid}>"
        )
