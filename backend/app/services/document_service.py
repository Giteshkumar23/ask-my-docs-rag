"""Document service — full implementation.

Encapsulates all database operations for the Document and DocumentChunk
models, keeping the API routers thin and testable.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import structlog
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.models.document import Document

log = structlog.get_logger(__name__)


class DocumentService:
    """Provides CRUD and status operations for Document records."""

    # ---------------------------------------------------------------------- #
    # Read operations
    # ---------------------------------------------------------------------- #

    @staticmethod
    async def get_document(db: AsyncSession, doc_id: uuid.UUID) -> Optional[Document]:
        """Return a single document by primary key, or ``None``."""
        result = await db.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_documents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        collection_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Tuple[List[Document], int]:
        """Return a paginated list of documents and total count.

        Optional filters: collection_id, status, file_type.
        """
        base = select(Document)
        count_query = select(func.count()).select_from(Document)

        if collection_id is not None:
            base = base.where(Document.collection_id == collection_id)
            count_query = count_query.where(Document.collection_id == collection_id)
        if status is not None:
            base = base.where(Document.status == status)
            count_query = count_query.where(Document.status == status)
        if file_type is not None:
            base = base.where(Document.file_type == file_type)
            count_query = count_query.where(Document.file_type == file_type)

        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        query = base.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        items = list(result.scalars().all())
        return items, total

    @staticmethod
    async def get_document_chunks(
        db: AsyncSession,
        doc_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[DocumentChunk]:
        """Return paginated chunks for a document."""
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == doc_id)
            .order_by(DocumentChunk.chunk_index)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ---------------------------------------------------------------------- #
    # Write operations
    # ---------------------------------------------------------------------- #

    @staticmethod
    async def create_document(
        db: AsyncSession,
        name: str,
        original_filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        collection_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None,
    ) -> Document:
        """Create and persist a new document record."""
        doc = Document(
            id=uuid.uuid4(),
            name=name,
            original_filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            collection_id=collection_id,
            metadata_=metadata or {},
            status="uploading",
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        log.info("document.created", doc_id=str(doc.id), name=name)
        return doc

    @staticmethod
    async def update_document_status(
        db: AsyncSession,
        doc_id: uuid.UUID,
        status: str,
        error_message: Optional[str] = None,
        num_chunks: Optional[int] = None,
        num_pages: Optional[int] = None,
        processing_time: Optional[float] = None,
    ) -> Optional[Document]:
        """Update processing status and optional metadata."""
        values: dict = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
        if error_message is not None:
            values["error_message"] = error_message
        if num_chunks is not None:
            values["num_chunks"] = num_chunks
        if num_pages is not None:
            values["num_pages"] = num_pages
        if processing_time is not None:
            values["processing_time"] = processing_time

        await db.execute(
            update(Document).where(Document.id == doc_id).values(**values)
        )
        await db.commit()
        result = await db.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_document(db: AsyncSession, doc_id: uuid.UUID) -> None:
        """Delete a document and cascade to its chunks (via DB constraint)."""
        await db.execute(delete(Document).where(Document.id == doc_id))
        await db.commit()
        log.info("document.deleted", doc_id=str(doc_id))
