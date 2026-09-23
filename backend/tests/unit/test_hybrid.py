"""Unit tests for the hybrid retriever."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.retrieval.bm25 import RetrievedChunk
from app.rag.retrieval.hybrid import HybridRetriever, RetrievalMetadata


def _make_chunk(chunk_id: uuid.UUID, doc_name: str, bm25: float, vec: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=uuid.uuid4(),
        document_name=doc_name,
        text=f"Text for {doc_name}",
        page_number=1,
        section=None,
        score=max(bm25, vec),
        retrieval_method="hybrid",
        bm25_score=bm25,
        vector_score=vec,
    )


class TestHybridRetriever:
    """Tests for :class:`HybridRetriever`."""

    def test_instantiation_requires_db_and_settings(self) -> None:
        mock_db = MagicMock()
        mock_settings = MagicMock()
        mock_settings.BM25_WEIGHT = 0.4
        mock_settings.VECTOR_WEIGHT = 0.6
        retriever = HybridRetriever(db=mock_db, settings=mock_settings)
        assert retriever is not None

    def test_rrf_fusion_deduplicates(self) -> None:
        """A chunk appearing in both BM25 and vector results should appear once."""
        mock_db = MagicMock()
        mock_settings = MagicMock()
        mock_settings.BM25_WEIGHT = 0.4
        mock_settings.VECTOR_WEIGHT = 0.6

        cid = uuid.uuid4()
        bm25_results = [_make_chunk(cid, "doc1", 0.9, 0.0)]
        vector_results = [_make_chunk(cid, "doc1", 0.0, 0.85)]

        retriever = HybridRetriever(db=mock_db, settings=mock_settings)
        fused = retriever._fuse(bm25_results, vector_results, top_k=10)

        # Should only appear once despite being in both lists
        ids = [c.chunk_id for c in fused]
        assert ids.count(cid) == 1

    def test_rrf_fusion_merges_distinct_chunks(self) -> None:
        """Chunks from different retrievers should all appear in fused output."""
        mock_db = MagicMock()
        mock_settings = MagicMock()
        mock_settings.BM25_WEIGHT = 0.4
        mock_settings.VECTOR_WEIGHT = 0.6

        cid1, cid2, cid3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        bm25_results = [_make_chunk(cid1, "doc1", 0.9, 0.0)]
        vector_results = [_make_chunk(cid2, "doc2", 0.0, 0.8), _make_chunk(cid3, "doc3", 0.0, 0.7)]

        retriever = HybridRetriever(db=mock_db, settings=mock_settings)
        fused = retriever._fuse(bm25_results, vector_results, top_k=10)

        fused_ids = {c.chunk_id for c in fused}
        assert cid1 in fused_ids
        assert cid2 in fused_ids
        assert cid3 in fused_ids

    def test_retrieval_metadata_dataclass(self) -> None:
        meta = RetrievalMetadata(
            bm25_count=5,
            vector_count=8,
            combined_count=10,
            retrieval_time=0.123,
        )
        assert meta.bm25_count == 5
        assert meta.combined_count == 10
