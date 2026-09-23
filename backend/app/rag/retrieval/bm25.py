"""BM25 keyword retriever — full implementation.

Builds a BM25Okapi index over all chunks (optionally scoped to a collection),
tokenises queries, and returns ranked :class:`RetrievedChunk` objects with
normalised scores.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import List, Optional

import structlog
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.models.document import Document

log = structlog.get_logger(__name__)


# --------------------------------------------------------------------------- #
# Shared data-class (also imported by vector.py and hybrid.py)
# --------------------------------------------------------------------------- #


@dataclass
class RetrievedChunk:
    """A single chunk returned by any retriever."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    text: str
    page_number: Optional[int]
    section: Optional[str]
    score: float
    retrieval_method: str  # "bm25" | "vector" | "hybrid"

    # Optional per-method scores stored by the hybrid retriever
    bm25_score: Optional[float] = None
    vector_score: Optional[float] = None


# --------------------------------------------------------------------------- #
# Tokeniser
# --------------------------------------------------------------------------- #


def _tokenize(text: str) -> List[str]:
    """Lowercase and split on whitespace/punctuation."""
    return re.split(r"[\s\W]+", text.lower())


# --------------------------------------------------------------------------- #
# BM25Retriever
# --------------------------------------------------------------------------- #


class BM25Retriever:
    """Sparse keyword retriever backed by BM25Okapi.

    The index is built lazily on the first retrieval call.  If
    ``collection_id`` changes between calls the index is rebuilt.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._index: Optional[BM25Okapi] = None
        self._chunk_ids: List[uuid.UUID] = []
        self._chunk_map: dict[uuid.UUID, RetrievedChunk] = {}
        self._current_collection_id: Optional[uuid.UUID] = None

    # ---------------------------------------------------------------------- #
    # Index management
    # ---------------------------------------------------------------------- #

    async def build_index(
        self, collection_id: Optional[uuid.UUID] = None
    ) -> None:
        """Load all chunks from DB (filtered by collection) and build index."""
        log.info("bm25.build_index", collection_id=str(collection_id))

        stmt = (
            select(DocumentChunk, Document.name.label("doc_name"))
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.status == "completed")
        )
        if collection_id is not None:
            stmt = stmt.where(Document.collection_id == collection_id)

        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            log.warning("bm25.build_index.empty", collection_id=str(collection_id))
            self._index = None
            self._chunk_ids = []
            self._chunk_map = {}
            self._current_collection_id = collection_id
            return

        corpus: List[List[str]] = []
        self._chunk_ids = []
        self._chunk_map = {}

        for chunk, doc_name in rows:
            tokens = _tokenize(chunk.text)
            corpus.append(tokens)
            self._chunk_ids.append(chunk.id)
            self._chunk_map[chunk.id] = RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=doc_name,
                text=chunk.text,
                page_number=chunk.page_number,
                section=chunk.section,
                score=0.0,
                retrieval_method="bm25",
            )

        self._index = BM25Okapi(corpus)
        self._current_collection_id = collection_id
        log.info("bm25.index_built", num_chunks=len(rows))

    # ---------------------------------------------------------------------- #
    # Retrieval
    # ---------------------------------------------------------------------- #

    async def retrieve(
        self,
        query: str,
        top_k: int = 20,
        collection_id: Optional[uuid.UUID] = None,
    ) -> List[RetrievedChunk]:
        """Score all chunks via BM25 and return the top-K with normalised scores."""
        if self._index is None or self._current_collection_id != collection_id:
            await self.build_index(collection_id)

        if self._index is None or not self._chunk_ids:
            return []

        query_tokens = _tokenize(query)
        raw_scores: List[float] = self._index.get_scores(query_tokens).tolist()

        # Pair and sort
        scored = sorted(
            zip(self._chunk_ids, raw_scores), key=lambda x: x[1], reverse=True
        )

        # Take top results that have a non-zero score
        top = [(cid, s) for cid, s in scored[:top_k] if s > 0]

        if not top:
            return []

        # Normalise scores to [0, 1]
        max_score = top[0][1]
        results: List[RetrievedChunk] = []
        for chunk_id, raw_score in top:
            base = self._chunk_map.get(chunk_id)
            if base is None:
                continue
            norm = raw_score / max_score if max_score > 0 else 0.0
            results.append(
                RetrievedChunk(
                    chunk_id=base.chunk_id,
                    document_id=base.document_id,
                    document_name=base.document_name,
                    text=base.text,
                    page_number=base.page_number,
                    section=base.section,
                    score=norm,
                    retrieval_method="bm25",
                    bm25_score=norm,
                )
            )

        log.debug("bm25.retrieve", query=query[:50], results=len(results))
        return results
