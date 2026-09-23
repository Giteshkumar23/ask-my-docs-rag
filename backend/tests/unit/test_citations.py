"""Unit tests for citation parsing and validation."""
from __future__ import annotations

import uuid

import pytest

from app.rag.citations.parser import ParsedCitation, parse_citations, parse_citations_detail
from app.rag.citations.validator import CitationValidator, ValidationResult
from app.rag.retrieval.bm25 import RetrievedChunk


def _make_chunk(n: int) -> RetrievedChunk:
    """Helper: build a minimal RetrievedChunk for testing."""
    return RetrievedChunk(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_name=f"doc{n}",
        text=f"Chunk text {n}",
        page_number=n,
        section=None,
        score=0.9,
        retrieval_method="hybrid",
    )


class TestCitationParser:
    """Tests for :func:`parse_citations` and :func:`parse_citations_detail`."""

    def test_parse_no_citations(self) -> None:
        result = parse_citations("This answer has no citations.")
        assert result == []

    def test_parse_single_citation(self) -> None:
        result = parse_citations("The answer is here [1].")
        assert result == [1]

    def test_parse_multiple_citations(self) -> None:
        result = parse_citations("From [1] and also [2] and finally [3].")
        assert result == [1, 2, 3]

    def test_parse_deduplicates(self) -> None:
        """parse_citations returns sorted unique numbers."""
        result = parse_citations("[1] is mentioned twice [1].")
        assert result == [1]

    def test_parse_sorted(self) -> None:
        result = parse_citations("[3] then [1] then [2].")
        assert result == [1, 2, 3]

    def test_parse_detail_preserves_position(self) -> None:
        answer = "Start [2] end."
        result = parse_citations_detail(answer)
        assert len(result) == 1
        assert result[0].citation_number == 2
        assert result[0].context_position == answer.index("[2]")

    def test_parse_detail_duplicate_citations(self) -> None:
        result = parse_citations_detail("[1] is mentioned twice [1].")
        assert len(result) == 2
        assert all(c.citation_number == 1 for c in result)


class TestCitationValidator:
    """Tests for :class:`CitationValidator`."""

    def test_all_valid(self) -> None:
        chunks = [_make_chunk(i) for i in range(3)]
        validator = CitationValidator()
        result = validator.validate("[1] fact A. [2] fact B. [3] fact C.", chunks)
        assert result.is_valid is True
        assert result.invalid_citations == []
        assert set(result.cited_indices) == {1, 2, 3}

    def test_out_of_range_citation_is_invalid(self) -> None:
        chunks = [_make_chunk(1)]  # only 1 chunk
        validator = CitationValidator()
        result = validator.validate("See [1] and also [5].", chunks, strict=True)
        assert result.is_valid is False
        assert 5 in result.invalid_citations

    def test_zero_citation_is_invalid(self) -> None:
        chunks = [_make_chunk(1)]
        validator = CitationValidator()
        result = validator.validate("See [0].", chunks, strict=True)
        assert result.is_valid is False
        assert 0 in result.invalid_citations

    def test_empty_answer(self) -> None:
        chunks = [_make_chunk(1), _make_chunk(2)]
        validator = CitationValidator()
        result = validator.validate("", chunks)
        assert result.cited_indices == []
        assert result.coverage == 0.0

    def test_coverage_calculation(self) -> None:
        chunks = [_make_chunk(i) for i in range(4)]
        validator = CitationValidator()
        # Only cite 2 out of 4 chunks
        result = validator.validate("[1] fact. [2] fact.", chunks)
        assert result.coverage == pytest.approx(2 / 4)
