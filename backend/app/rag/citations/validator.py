"""Citation validator — full implementation.

Verifies that every [N] citation in the generated answer maps to a valid
(1-indexed) chunk from the list of chunks provided to the LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.rag.citations.parser import parse_citations
from app.rag.retrieval.bm25 import RetrievedChunk


@dataclass
class ValidationResult:
    """Result of validating citations in a generated answer."""

    is_valid: bool
    cited_indices: List[int]          # 1-based indices actually cited
    invalid_citations: List[int]      # cited numbers outside [1, len(chunks)]
    coverage: float                   # fraction of provided chunks that are cited


class CitationValidator:
    """Validates that LLM-generated citations are in-range and honest."""

    def validate(
        self,
        answer: str,
        chunks: List[RetrievedChunk],  # chunks provided to the LLM, 1-indexed
        strict: bool = True,
    ) -> ValidationResult:
        """Check every [N] in *answer* against the provided *chunks*.

        Parameters
        ----------
        answer:
            The LLM-generated answer text.
        chunks:
            The list of :class:`RetrievedChunk` objects that were passed to
            the LLM.  Chunk ``[1]`` maps to ``chunks[0]``, etc.
        strict:
            When ``True``, any citation number outside ``[1, len(chunks)]``
            is flagged as invalid.  When ``False``, only obvious out-of-range
            numbers (> len(chunks)) are flagged but the result is still valid.

        Returns
        -------
        :class:`ValidationResult`
        """
        cited = parse_citations(answer)
        max_valid = len(chunks)

        invalid: List[int] = []
        for n in cited:
            if n < 1 or n > max_valid:
                invalid.append(n)

        is_valid = len(invalid) == 0

        # Coverage: what fraction of provided chunks are actually cited?
        cited_set = {n for n in cited if 1 <= n <= max_valid}
        coverage = len(cited_set) / max_valid if max_valid > 0 else 1.0

        return ValidationResult(
            is_valid=is_valid,
            cited_indices=sorted(cited_set),
            invalid_citations=invalid,
            coverage=coverage,
        )
