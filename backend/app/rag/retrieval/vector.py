"""Vector (dense) retriever — full implementation.

Encodes queries with SentenceTransformer, then uses pgvector's cosine
distance operator (<=>) to find the closest chunk embeddings in PostgreSQL.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

import structlog
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.rag.retrieval.bm25 import RetrievedChunk

log = structlog.get_logger(__name__)

# Reuse the same process-level model cache defined in pipeline.py
_model_cache: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str) -> SentenceTransformer:
    if model_name not in _model_cache:
        log.info("embedding.model.load", model=model_name)
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


class VectorRetriever:
    """Dense vector retriever using pgvector cosine distance.

    Parameters
    ----------
    db:
        An open :class:`AsyncSession`.
    settings:
        Application settings (embedding model name, etc.).
    """

    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    async def retrieve(
        self,
        query: str,
        top_k: int = 20,
        collection_id: Optional[uuid.UUID] = None,
    ) -> List[RetrievedChunk]:
        """Encode the query, then query pgvector for the nearest chunks.

        Returns chunks sorted by cosine similarity (highest first) with
        scores normalised to [0, 1].
        """
        model = _get_model(self.settings.EMBEDDING_MODEL)
        query_vec = model.encode(query, show_progress_bar=False, convert_to_numpy=True)
        query_vec_list = query_vec.tolist()

        # Build the SQL query.  pgvector's <=> operator returns cosine
        # *distance* (0 = identical, 2 = opposite), so similarity = 1 - dist.
        if collection_id is not None:
            sql = text(
                """
                SELECT
                    dc.id          AS chunk_id,
                    dc.document_id,
                    d.name         AS document_name,
                    dc.text,
                    dc.page_number,
                    dc.section,
                    1 - (dc.embedding <=> CAST(:query_vec AS vector)) AS cosine_sim
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE d.status = 'completed'
                  AND d.collection_id = :collection_id
                  AND dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> CAST(:query_vec AS vector)
                LIMIT :top_k
                """
            )
            params = {
                "query_vec": str(query_vec_list),
                "collection_id": str(collection_id),
                "top_k": top_k,
            }
        else:
            sql = text(
                """
                SELECT
                    dc.id          AS chunk_id,
                    dc.document_id,
                    d.name         AS document_name,
                    dc.text,
                    dc.page_number,
                    dc.section,
                    1 - (dc.embedding <=> CAST(:query_vec AS vector)) AS cosine_sim
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE d.status = 'completed'
                  AND dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> CAST(:query_vec AS vector)
                LIMIT :top_k
                """
            )
            params = {
                "query_vec": str(query_vec_list),
                "top_k": top_k,
            }

        result = await self.db.execute(sql, params)
        rows = result.mappings().all()

        if not rows:
            return []

        chunks: List[RetrievedChunk] = []
        for row in rows:
            sim = float(row["cosine_sim"])
            # Clamp to [0, 1] — floating-point arithmetic can produce tiny negatives
            sim = max(0.0, min(1.0, sim))
            chunks.append(
                RetrievedChunk(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    document_name=row["document_name"],
                    text=row["text"],
                    page_number=row["page_number"],
                    section=row["section"],
                    score=sim,
                    retrieval_method="vector",
                    vector_score=sim,
                )
            )

        log.debug("vector.retrieve", query=query[:50], results=len(chunks))
        return chunks
