"""Unit tests for the BM25 retriever."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.retrieval.bm25 import BM25Retriever, RetrievedChunk, _tokenize


class TestTokenize:
    """Tests for the BM25 tokeniser."""

    def test_lowercases(self) -> None:
        tokens = _tokenize("Hello World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_splits_on_punctuation(self) -> None:
        tokens = _tokenize("hello, world! foo.bar")
        assert "hello" in tokens
        assert "world" in tokens
        assert "foo" in tokens
        assert "bar" in tokens

    def test_empty_string(self) -> None:
        tokens = _tokenize("")
        # re.split on empty → [''] filter handles it
        assert isinstance(tokens, list)


class TestBM25Retriever:
    """Tests for :class:`BM25Retriever`."""

    def test_instantiation_requires_db(self) -> None:
        """BM25Retriever now requires a db session argument."""
        mock_db = MagicMock()
        retriever = BM25Retriever(db=mock_db)
        assert retriever is not None
        assert retriever._index is None

    @pytest.mark.asyncio
    async def test_retrieve_returns_empty_when_no_index(self) -> None:
        """Returns [] immediately when no chunks are in DB."""
        mock_db = AsyncMock()
        # Simulate empty DB result
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        retriever = BM25Retriever(db=mock_db)
        results = await retriever.retrieve("test query")
        assert results == []

    def test_retrieved_chunk_dataclass(self) -> None:
        chunk = RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            document_name="test.pdf",
            text="Some text",
            page_number=1,
            section="Introduction",
            score=0.8,
            retrieval_method="bm25",
        )
        assert chunk.score == 0.8
        assert chunk.bm25_score is None
        assert chunk.vector_score is None
