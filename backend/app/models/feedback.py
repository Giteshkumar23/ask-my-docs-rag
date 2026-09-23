"""SQLAlchemy ORM model for user feedback on query answers."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Feedback(Base):
    """User-provided rating and optional comment for a :class:`Query` response."""

    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # positive | negative
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_category: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # e.g. wrong_answer | missing_citation | hallucination | irrelevant
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    query: Mapped["Query"] = relationship(  # noqa: F821
        "Query", back_populates="feedback"
    )

    def __repr__(self) -> str:
        return (
            f"<Feedback id={self.id!s} query={self.query_id!s} "
            f"rating={self.rating!r}>"
        )
