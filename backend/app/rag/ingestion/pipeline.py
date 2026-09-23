"""Ingestion pipeline — full implementation.

Orchestrates the full document processing lifecycle:
  parse → chunk → embed (batch) → save to DB → update status
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np
import structlog
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.rag.ingestion.chunker import DocumentChunker
from app.rag.ingestion.parsers import DocumentParser

log = structlog.get_logger(__name__)

# Module-level model cache so the model is only loaded once per process.
_model_cache: dict[str, SentenceTransformer] = {}

_EMBEDDING_BATCH_SIZE = 32


def _get_model(model_name: str) -> SentenceTransformer:
    if model_name not in _model_cache:
        log.info("embedding.model.load", model=model_name)
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


class IngestionPipeline:
    """End-to-end document ingestion orchestrator.

    Parameters
    ----------
    db:
        An open :class:`AsyncSession`.
    settings:
        Application settings (embedding model name, chunk config, etc.).
    """

    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.parser = DocumentParser()
        self.chunker = DocumentChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    async def ingest(
        self,
        document_id: uuid.UUID,
        file_path: str,
        file_type: str,
    ) -> None:
        """Run the full ingestion pipeline for one document.

        Status transitions:
            processing → chunking → embedding → indexing → completed
            (or failed on any error)
        """
        start_time = time.perf_counter()
        log.info("ingestion.start", document_id=str(document_id), file_type=file_type)

        try:
            # ---------------------------------------------------------------- #
            # 1. Mark as processing
            # ---------------------------------------------------------------- #
            await self._update_status(document_id, "processing")

            # ---------------------------------------------------------------- #
            # 2. Parse document
            # ---------------------------------------------------------------- #
            parsed_doc = self.parser.parse(file_path)
            log.info(
                "ingestion.parsed",
                document_id=str(document_id),
                num_pages=parsed_doc.num_pages,
            )

            # ---------------------------------------------------------------- #
            # 3. Mark as chunking
            # ---------------------------------------------------------------- #
            await self._update_status(document_id, "chunking")

            # ---------------------------------------------------------------- #
            # 4. Chunk document
            # ---------------------------------------------------------------- #
            chunks = self.chunker.chunk_document(parsed_doc)
            log.info(
                "ingestion.chunked",
                document_id=str(document_id),
                num_chunks=len(chunks),
            )

            # ---------------------------------------------------------------- #
            # 5. Mark as embedding
            # ---------------------------------------------------------------- #
            await self._update_status(document_id, "embedding")

            # ---------------------------------------------------------------- #
            # 6. Generate embeddings
            # ---------------------------------------------------------------- #
            texts = [c.text for c in chunks]
            embeddings = self._embed_texts(texts)

            # ---------------------------------------------------------------- #
            # 7. Mark as indexing
            # ---------------------------------------------------------------- #
            await self._update_status(document_id, "indexing")

            # ---------------------------------------------------------------- #
            # 8. Save chunks with embeddings to DB
            # ---------------------------------------------------------------- #
            await self._save_chunks(document_id, chunks, embeddings)

            # ---------------------------------------------------------------- #
            # 9. Finalize document record
            # ---------------------------------------------------------------- #
            processing_time = time.perf_counter() - start_time
            await self._finalize(
                document_id=document_id,
                num_chunks=len(chunks),
                num_pages=parsed_doc.num_pages,
                processing_time=processing_time,
            )
            log.info(
                "ingestion.complete",
                document_id=str(document_id),
                num_chunks=len(chunks),
                elapsed_s=round(processing_time, 2),
            )

        except Exception as exc:  # noqa: BLE001
            log.exception(
                "ingestion.failed", document_id=str(document_id), error=str(exc)
            )
            await self._fail(document_id, str(exc))
            raise

    # ---------------------------------------------------------------------- #
    # Embedding helpers
    # ---------------------------------------------------------------------- #

    def _embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Encode all texts in batches; returns one numpy array per text."""
        model = _get_model(self.settings.EMBEDDING_MODEL)
        all_embeddings: List[np.ndarray] = []
        for i in range(0, len(texts), _EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + _EMBEDDING_BATCH_SIZE]
            vecs = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
            all_embeddings.extend(vecs)
        return all_embeddings

    # ---------------------------------------------------------------------- #
    # DB helpers
    # ---------------------------------------------------------------------- #

    async def _update_status(self, document_id: uuid.UUID, status: str) -> None:
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(
                status=status,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _finalize(
        self,
        document_id: uuid.UUID,
        num_chunks: int,
        num_pages: int,
        processing_time: float,
    ) -> None:
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(
                status="completed",
                num_chunks=num_chunks,
                num_pages=num_pages,
                processing_time=processing_time,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _fail(self, document_id: uuid.UUID, error_message: str) -> None:
        try:
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(
                    status="failed",
                    error_message=error_message[:2048],
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await self.db.execute(stmt)
            await self.db.commit()
        except Exception:  # noqa: BLE001
            log.exception("ingestion.fail_update_error", document_id=str(document_id))

    async def _save_chunks(
        self,
        document_id: uuid.UUID,
        chunks: list,
        embeddings: List[np.ndarray],
    ) -> None:
        """Bulk-insert DocumentChunk rows with their embeddings."""
        # Delete any pre-existing chunks for this document (re-index case)
        from sqlalchemy import delete  # noqa: PLC0415
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

        db_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            db_chunks.append(
                DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    token_count=chunk.token_count,
                    embedding=embedding.tolist(),
                )
            )

        self.db.add_all(db_chunks)
        await self.db.commit()
        log.debug(
            "ingestion.chunks_saved",
            document_id=str(document_id),
            count=len(db_chunks),
        )
