"""SQLAlchemy ORM models for RAG evaluation runs and per-question results."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EvaluationRun(Base):
    """An evaluation run executed against a benchmark dataset."""

    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    dataset_name: Mapped[str] = mapped_column(String(256), nullable=False)

    # Retrieval metrics
    recall_at_5: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision_at_5: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mrr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hit_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Generation / RAG metrics
    faithfulness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    answer_relevance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    context_relevance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Citation metrics
    citation_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    citation_coverage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Latency metrics (seconds)
    avg_retrieval_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_reranking_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_generation_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_total_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    num_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    results: Mapped[list["EvaluationResult"]] = relationship(
        "EvaluationResult", back_populates="run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationRun id={self.id!s} name={self.name!r} "
            f"passed={self.passed} questions={self.num_questions}>"
        )


class EvaluationResult(Base):
    """A per-question result within an :class:`EvaluationRun`."""

    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    generated_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_sources: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    retrieved_sources: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    faithfulness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    citation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retrieval_recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    run: Mapped["EvaluationRun"] = relationship("EvaluationRun", back_populates="results")

    def __repr__(self) -> str:
        return (
            f"<EvaluationResult id={self.id!s} run={self.run_id!s} "
            f"faithfulness={self.faithfulness_score}>"
        )
