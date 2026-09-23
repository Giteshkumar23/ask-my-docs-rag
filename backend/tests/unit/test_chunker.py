"""Unit tests for the text chunker."""
from __future__ import annotations

import pytest

from app.rag.ingestion.chunker import ChunkData, DocumentChunker
from app.rag.ingestion.parsers import ParsedDocument, ParsedPage


class TestDocumentChunker:
    """Tests for :class:`DocumentChunker`."""

    def test_instantiation(self) -> None:
        chunker = DocumentChunker(chunk_size=256, chunk_overlap=32)
        assert chunker.chunk_size == 256
        assert chunker.chunk_overlap == 32

    def test_chunk_short_text_single_chunk(self) -> None:
        chunker = DocumentChunker(chunk_size=512, chunk_overlap=64)
        chunks = chunker.chunk_text("Hello world, this is a short test.")
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world, this is a short test."
        assert chunks[0].chunk_index == 0
        assert chunks[0].token_count > 0

    def test_chunk_data_defaults(self) -> None:
        chunk = ChunkData(text="hello", chunk_index=0)
        assert chunk.token_count == 0
        assert chunk.page_number is None
        assert chunk.section is None

    def test_chunk_preserves_page_number(self) -> None:
        chunker = DocumentChunker(chunk_size=512)
        chunks = chunker.chunk_text("Some text.", page_number=3, section="Intro")
        assert all(c.page_number == 3 for c in chunks)
        assert all(c.section == "Intro" for c in chunks)

    def test_chunk_document_multiple_pages(self) -> None:
        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=1, text="Page one content here."),
                ParsedPage(page_number=2, text="Page two content here."),
            ],
            num_pages=2,
        )
        chunker = DocumentChunker(chunk_size=512)
        chunks = chunker.chunk_document(doc)
        assert len(chunks) >= 2
        page_numbers = {c.page_number for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_long_text_produces_multiple_chunks(self) -> None:
        """Text with many words should be split into multiple chunks."""
        # ~200 words × 1.3 ≈ 260 tokens → should split into 2 chunks at size 150
        words = " ".join(["word"] * 200)
        chunker = DocumentChunker(chunk_size=150, chunk_overlap=20)
        chunks = chunker.chunk_text(words)
        assert len(chunks) >= 2

    def test_overlap_words_appear_in_consecutive_chunks(self) -> None:
        """The last words of chunk N should appear at the start of chunk N+1."""
        words = " ".join([f"word{i}" for i in range(200)])
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=30)
        chunks = chunker.chunk_text(words)
        if len(chunks) >= 2:
            first_chunk_words = set(chunks[0].text.split())
            second_chunk_words = set(chunks[1].text.split())
            overlap = first_chunk_words & second_chunk_words
            assert len(overlap) > 0, "Expected overlap between consecutive chunks"
