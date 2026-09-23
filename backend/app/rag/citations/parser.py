"""Citation parser — full implementation.

Extracts all [N] citation markers from LLM-generated answer text and
returns them as a sorted, deduplicated list of citation numbers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class ParsedCitation:
    """A citation extracted from generated text."""

    citation_number: int
    context_position: int  # character offset of the opening bracket


def parse_citations_detail(answer: str) -> List[ParsedCitation]:
    """Extract all ``[N]`` citation markers from *answer* with positions.

    Returns a list of :class:`ParsedCitation` in order of appearance,
    including duplicates (same number at different positions).
    """
    results: List[ParsedCitation] = []
    for match in re.finditer(r"\[(\d+)\]", answer):
        results.append(
            ParsedCitation(
                citation_number=int(match.group(1)),
                context_position=match.start(),
            )
        )
    return results


def parse_citations(answer: str) -> List[int]:
    """Return sorted unique citation numbers found in *answer*.

    Example
    -------
    >>> parse_citations("Fact A [1] and fact B [2][1].")
    [1, 2]
    """
    found = {int(m) for m in re.findall(r"\[(\d+)\]", answer)}
    return sorted(found)
