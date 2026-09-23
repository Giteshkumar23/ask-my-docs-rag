"""Hybrid (BM25 + vector) retriever with Reciprocal Rank Fusion — full implementation.

Runs BM25 and vector retrieval in parallel, fuses the ranked lists using
Reciprocal Rank Fusion (RRF) and a weighted score, then returns the merged
top-K results together with retrieval metadata.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.rag.retrieval.bm25 import BM25Retriever, RetrievedChunk
from app.rag.retrieval.vector import VectorRetriever

log = structlog.get_logger(__name__)

_RRF_K = 60  # Standard RRF constant


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #


@dataclass
class RetrievalMetadata:
    """Summary statistics from a hybrid retrieval call."""

    bm25_count: int
    vector_count: int
    combined_count: int
    retrieval_time: float  # seconds


# --------------------------------------------------------------------------- #
# HybridRetriever
# --------------------------------------------------------------------------- #


class HybridRetriever:
    """Combines BM25 and vector scores via Reciprocal Rank Fusion.

    Parameters
    ----------
    db:
        An open :class:`AsyncSession`.
    settings:
        Application settings (BM25_WEIGHT, VECTOR_WEIGHT, etc.).
    """

    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self._bm25 = BM25Retriever(db)
        self._vector = VectorRetriever(db, settings)

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    async def retrieve(
        self,
        query: str,
        top_k: int = 20,
        collection_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[RetrievedChunk], RetrievalMetadata]:
        """Run both retrievers in parallel and fuse with RRF.

        Returns
        -------
        (results, metadata)
            *results* — top_k :class:`RetrievedChunk` objects, each tagged
            with ``retrieval_method="hybrid"`` and all per-method scores.
            *metadata* — :class:`RetrievalMetadata` with counts and timing.
        """
        t0 = time.perf_counter()

        bm25_results, vector_results = await asyncio.gather(
            self._bm25.retrieve(query, top_k=top_k, collection_id=collection_id),
            self._vector.retrieve(query, top_k=top_k, collection_id=collection_id),
        )

        fused = self._fuse(bm25_results, vector_results, top_k=top_k)

        metadata = RetrievalMetadata(
            bm25_count=len(bm25_results),
            vector_count=len(vector_results),
            combined_count=len(fused),
            retrieval_time=time.perf_counter() - t0,
        )

        log.debug(
            "hybrid.retrieve",
            query=query[:50],
            bm25=len(bm25_results),
            vector=len(vector_results),
            fused=len(fused),
        )
        return fused, metadata

    # ---------------------------------------------------------------------- #
    # Fusion
    # ---------------------------------------------------------------------- #

    def _fuse(
        self,
        bm25_results: List[RetrievedChunk],
        vector_results: List[RetrievedChunk],
        top_k: int,
    ) -> List[RetrievedChunk]:
        """Merge two ranked lists using Reciprocal Rank Fusion.

        RRF_score(d) = Σ  1 / (k + rank(d))   for each list containing d
        where k = 60 (standard value that damps the effect of high ranks).

        Additionally computes a weighted combination:
            hybrid_score = bm25_weight * norm_bm25 + vector_weight * norm_vector
        """
        bm25_weight = self.settings.BM25_WEIGHT
        vector_weight = self.settings.VECTOR_WEIGHT

        # Build lookup by chunk_id
        bm25_by_id: Dict[uuid.UUID, Tuple[int, RetrievedChunk]] = {
            c.chunk_id: (rank, c) for rank, c in enumerate(bm25_results, start=1)
        }
        vector_by_id: Dict[uuid.UUID, Tuple[int, RetrievedChunk]] = {
            c.chunk_id: (rank, c) for rank, c in enumerate(vector_results, start=1)
        }

        all_ids = set(bm25_by_id) | set(vector_by_id)

        scored: List[Tuple[float, float, uuid.UUID]] = []
        for chunk_id in all_ids:
            rrf_score = 0.0
            bm25_norm = 0.0
            vector_norm = 0.0

            if chunk_id in bm25_by_id:
                rank, _ = bm25_by_id[chunk_id]
                rrf_score += 1.0 / (_RRF_K + rank)
                bm25_norm = bm25_by_id[chunk_id][1].bm25_score or 0.0

            if chunk_id in vector_by_id:
                rank, _ = vector_by_id[chunk_id]
                rrf_score += 1.0 / (_RRF_K + rank)
                vector_norm = vector_by_id[chunk_id][1].vector_score or 0.0

            weighted = bm25_weight * bm25_norm + vector_weight * vector_norm
            # Use RRF as primary sort, weighted as secondary signal
            final_score = 0.7 * rrf_score * 100 + 0.3 * weighted
            scored.append((final_score, rrf_score, chunk_id))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_ids = [cid for _, _, cid in scored[:top_k]]

        results: List[RetrievedChunk] = []
        for chunk_id in top_ids:
            # Prefer the chunk object from vector results (richer metadata);
            # fall back to bm25 result.
            if chunk_id in vector_by_id:
                base = vector_by_id[chunk_id][1]
            else:
                base = bm25_by_id[chunk_id][1]

            bm25_s = bm25_by_id[chunk_id][1].bm25_score if chunk_id in bm25_by_id else None
            vector_s = vector_by_id[chunk_id][1].vector_score if chunk_id in vector_by_id else None

            # Compute final normalised score
            rrf_raw = next(rrf for _, rrf, cid in scored if cid == chunk_id)

            results.append(
                RetrievedChunk(
                    chunk_id=base.chunk_id,
                    document_id=base.document_id,
                    document_name=base.document_name,
                    text=base.text,
                    page_number=base.page_number,
                    section=base.section,
                    score=rrf_raw,
                    retrieval_method="hybrid",
                    bm25_score=bm25_s,
                    vector_score=vector_s,
                )
            )

        return results
