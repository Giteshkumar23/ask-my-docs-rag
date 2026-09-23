"""Recursive character-level text chunker.

Splits a :class:`ParsedDocument` into overlapping chunks that respect a
configurable ``chunk_size`` (measured in approximate tokens) and
``chunk_overlap``.  The algorithm is a recursive descent that tries each
separator in order, splitting only when the current segment exceeds
``chunk_size``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog

from app.rag.ingestion.parsers import ParsedDocument, ParsedPage

log = structlog.get_logger(__name__)

_DEFAULT_SEPARATORS: List[str] = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]


# --------------------------------------------------------------------------- #
# Data-class
# --------------------------------------------------------------------------- #


@dataclass
class ChunkData:
    """A single text chunk ready for embedding and storage."""

    text: str
    chunk_index: int
    page_number: Optional[int] = None
    section: Optional[str] = None
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Chunker
# --------------------------------------------------------------------------- #


class DocumentChunker:
    """Split parsed pages into overlapping token-bounded chunks.

    Parameters
    ----------
    chunk_size:
        Approximate maximum token count per chunk.
    chunk_overlap:
        Number of tokens to repeat at the start of the next chunk.
    separators:
        Ordered list of separators to try; falls back to the next one
        when the split does not reduce chunk size below ``chunk_size``.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separators: Optional[List[str]] = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators if separators is not None else _DEFAULT_SEPARATORS

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    def chunk_document(self, doc: ParsedDocument) -> List[ChunkData]:
        """Chunk all pages of a :class:`ParsedDocument`.

        Each page is chunked independently so that ``page_number`` and
        ``section`` are preserved on every resulting chunk.
        """
        all_chunks: List[ChunkData] = []
        global_index = 0
        for page in doc.pages:
            page_chunks = self._chunk_page(page, start_index=global_index)
            all_chunks.extend(page_chunks)
            global_index += len(page_chunks)
        log.debug(
            "chunker.complete",
            total_chunks=len(all_chunks),
            num_pages=doc.num_pages,
        )
        return all_chunks

    def chunk_text(
        self,
        text: str,
        page_number: Optional[int] = None,
        section: Optional[str] = None,
        start_index: int = 0,
    ) -> List[ChunkData]:
        """Chunk a raw string directly (useful for testing)."""
        page = ParsedPage(
            page_number=page_number or 1, text=text, section=section
        )
        return self._chunk_page(page, start_index=start_index)

    # ---------------------------------------------------------------------- #
    # Internal helpers
    # ---------------------------------------------------------------------- #

    @staticmethod
    def _approx_tokens(text: str) -> int:
        """Approximate token count: word count × 1.3, rounded up."""
        words = len(text.split())
        return max(1, int(words * 1.3 + 0.5))

    def _chunk_page(self, page: ParsedPage, start_index: int = 0) -> List[ChunkData]:
        """Split one page's text into chunks."""
        raw_chunks = self._split(page.text, self.separators)
        merged = self._merge_with_overlap(raw_chunks)
        result: List[ChunkData] = []
        for i, text in enumerate(merged):
            text = text.strip()
            if not text:
                continue
            result.append(
                ChunkData(
                    text=text,
                    chunk_index=start_index + i,
                    page_number=page.page_number,
                    section=page.section,
                    token_count=self._approx_tokens(text),
                )
            )
        return result

    def _split(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split *text* using the first usable separator."""
        if self._approx_tokens(text) <= self.chunk_size:
            return [text]

        if not separators:
            # No separator left — hard-split by words
            return self._hard_split(text)

        sep = separators[0]
        rest = separators[1:]

        if sep == "":
            # Last-resort: split on individual characters
            return self._hard_split(text)

        parts = text.split(sep)
        if len(parts) == 1:
            # Separator not found; try next
            return self._split(text, rest)

        final: List[str] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if self._approx_tokens(part) > self.chunk_size:
                # Recursively split this part with remaining separators
                final.extend(self._split(part, rest))
            else:
                final.append(part)
        return final

    def _hard_split(self, text: str) -> List[str]:
        """Split text into word-count windows when no separator works."""
        words = text.split()
        window = int(self.chunk_size / 1.3)
        chunks: List[str] = []
        start = 0
        while start < len(words):
            chunk_words = words[start : start + window]
            chunks.append(" ".join(chunk_words))
            start += window
        return chunks

    def _merge_with_overlap(self, splits: List[str]) -> List[str]:
        """Merge small splits and add overlap between consecutive chunks.

        Splits are greedily merged until adding the next split would exceed
        ``chunk_size``.  The overlap is taken from the end of the previous
        chunk using word-level granularity.
        """
        if not splits:
            return []

        chunks: List[str] = []
        current_words: List[str] = []
        current_tokens = 0
        overlap_words = int(self.chunk_overlap / 1.3)

        for split in splits:
            split_tokens = self._approx_tokens(split)
            if current_tokens + split_tokens > self.chunk_size and current_words:
                chunks.append(" ".join(current_words))
                # Seed next chunk with overlap from end of current
                current_words = current_words[-overlap_words:] if overlap_words else []
                current_tokens = self._approx_tokens(" ".join(current_words))
            current_words.extend(split.split())
            current_tokens = self._approx_tokens(" ".join(current_words))

        if current_words:
            chunks.append(" ".join(current_words))

        return chunks
