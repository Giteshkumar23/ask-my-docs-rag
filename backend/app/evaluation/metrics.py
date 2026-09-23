"""RAG evaluation metrics — full implementation.

Retrieval metrics:
  recall_at_k, precision_at_k, mean_reciprocal_rank, hit_rate

Citation metrics:
  citation_accuracy, citation_coverage, citation_accuracy_by_index

Generation metrics (heuristic, keyword-based):
  compute_faithfulness, compute_answer_relevance
"""
from __future__ import annotations

import re
from typing import List, TypeVar, Union
import uuid

T = TypeVar("T")


# --------------------------------------------------------------------------- #
# Retrieval metrics
# --------------------------------------------------------------------------- #


def recall_at_k(
    retrieved: List,
    relevant: List,
    k: int = 5,
) -> float:
    """Compute Recall@K.

    Parameters
    ----------
    retrieved:
        Ordered list of retrieved items (top K will be taken).
    relevant:
        Ground-truth relevant items.
    k:
        Cutoff.
    """
    if not relevant:
        return 0.0
    top_k = set(str(x) for x in retrieved[:k])
    rel_set = set(str(x) for x in relevant)
    return len(top_k & rel_set) / len(rel_set)


def precision_at_k(
    retrieved: List,
    relevant: List,
    k: int = 5,
) -> float:
    """Compute Precision@K."""
    if k == 0:
        return 0.0
    top_k = set(str(x) for x in retrieved[:k])
    rel_set = set(str(x) for x in relevant)
    return len(top_k & rel_set) / k


def mean_reciprocal_rank(
    retrieved: List,
    relevant: List,
) -> float:
    """Compute MRR (position of first relevant hit)."""
    rel_set = set(str(x) for x in relevant)
    for rank, item in enumerate(retrieved, start=1):
        if str(item) in rel_set:
            return 1.0 / rank
    return 0.0


def hit_rate(
    retrieved: List,
    relevant: List,
    k: int = 5,
) -> float:
    """Return 1.0 if at least one relevant item is in the top-K, else 0.0."""
    top_k = set(str(x) for x in retrieved[:k])
    rel_set = set(str(x) for x in relevant)
    return 1.0 if top_k & rel_set else 0.0


# --------------------------------------------------------------------------- #
# Citation metrics
# --------------------------------------------------------------------------- #


def citation_accuracy(
    cited_chunk_ids: List,
    retrieved_chunk_ids: List,
) -> float:
    """Fraction of cited chunks that were actually retrieved."""
    if not cited_chunk_ids:
        return 1.0
    retrieved_set = set(str(x) for x in retrieved_chunk_ids)
    valid = sum(1 for c in cited_chunk_ids if str(c) in retrieved_set)
    return valid / len(cited_chunk_ids)


def citation_coverage(
    cited_chunk_ids: List,
    used_chunk_ids: List,
) -> float:
    """Fraction of used chunks that appear as explicit citations."""
    if not used_chunk_ids:
        return 1.0
    cited_set = set(str(x) for x in cited_chunk_ids)
    covered = sum(1 for u in used_chunk_ids if str(u) in cited_set)
    return covered / len(used_chunk_ids)


def citation_accuracy_by_index(
    cited_indices: List[int],
    total_chunks: int,
) -> float:
    """Fraction of cited [N] indices that are within range [1, total_chunks].

    Used when we have citation numbers but not chunk IDs.
    """
    if not cited_indices:
        return 1.0
    valid = sum(1 for n in cited_indices if 1 <= n <= total_chunks)
    return valid / len(cited_indices)


# --------------------------------------------------------------------------- #
# Generation metrics (heuristic, no LLM judge)
# --------------------------------------------------------------------------- #


def _extract_keywords(text: str) -> set:
    """Lower-case word tokens, stripped of punctuation."""
    return set(re.findall(r"\b\w+\b", text.lower()))


def compute_faithfulness(answer: str, context_chunks: List[str]) -> float:
    """Heuristic faithfulness: fraction of answer sentences whose keywords
    overlap with at least one context chunk.

    A sentence is considered "supported" if ≥40% of its keywords appear
    in any single context chunk.
    """
    if not answer or not context_chunks:
        return 0.0

    # Tokenise all context chunks once
    context_keywords = [_extract_keywords(c) for c in context_chunks]

    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    if not sentences:
        return 0.0

    supported = 0
    for sentence in sentences:
        sent_kw = _extract_keywords(sentence)
        if not sent_kw:
            supported += 1  # empty / punctuation-only
            continue
        for ctx_kw in context_keywords:
            overlap = len(sent_kw & ctx_kw) / len(sent_kw)
            if overlap >= 0.4:
                supported += 1
                break

    return supported / len(sentences)


def compute_answer_relevance(question: str, answer: str) -> float:
    """Heuristic relevance: keyword overlap between question and answer.

    Returns the Jaccard similarity of question and answer keyword sets.
    """
    if not question or not answer:
        return 0.0
    q_kw = _extract_keywords(question)
    a_kw = _extract_keywords(answer)
    if not q_kw:
        return 0.0
    intersection = q_kw & a_kw
    union = q_kw | a_kw
    return len(intersection) / len(union) if union else 0.0
