"""Cross-encoder reranker — full implementation.

Loads a CrossEncoder model (lazily, once per process) and scores
(query, chunk_text) pairs to produce a more precise relevance ranking
than the first-stage retrieval.
"""
from __future__ import annotations

import math
from typing import ClassVar, Dict, List, Optional

import structlog

from app.rag.retrieval.bm25 import RetrievedChunk

log = structlog.get_logger(__name__)


def _sigmoid(x: float) -> float:
    """Sigmoid function — maps logit score to (0, 1)."""
    return 1.0 / (1.0 + math.exp(-x))


class CrossEncoderReranker:
    """Reranks candidate chunks using a cross-encoder model.

    The model is loaded once and cached at the class level so repeated
    instantiations do not reload weights.

    Parameters
    ----------
    model_name:
        HuggingFace model identifier.
    """

    # Class-level model cache: model_name → CrossEncoder instance
    _model_cache: ClassVar[Dict[str, object]] = {}

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2",
    ) -> None:
        self.model_name = model_name

    # ---------------------------------------------------------------------- #
    # Lazy model loading
    # ---------------------------------------------------------------------- #

    def _get_model(self):  # type: ignore[return]
        """Return (and cache) the CrossEncoder model."""
        if self.model_name not in self.__class__._model_cache:
            from sentence_transformers import CrossEncoder  # noqa: PLC0415

            log.info("reranker.model.load", model=self.model_name)
            self.__class__._model_cache[self.model_name] = CrossEncoder(
                self.model_name
            )
        return self.__class__._model_cache[self.model_name]

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Score each (query, chunk_text) pair and return the top-K.

        1. Build (query, text) pairs.
        2. Run the cross-encoder in a single batch.
        3. Apply sigmoid to convert logits → [0, 1].
        4. Sort descending, take top_k.
        5. Set ``chunk.score`` to the reranker score.
        """
        if not chunks:
            return []

        model = self._get_model()
        pairs = [(query, chunk.text) for chunk in chunks]

        raw_scores: List[float] = model.predict(pairs, show_progress_bar=False).tolist()  # type: ignore[union-attr]

        # Attach scores
        scored = list(zip(raw_scores, chunks))
        scored.sort(key=lambda x: x[0], reverse=True)

        results: List[RetrievedChunk] = []
        for raw_score, chunk in scored[:top_k]:
            norm_score = _sigmoid(raw_score)
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    score=norm_score,
                    retrieval_method=chunk.retrieval_method,
                    bm25_score=chunk.bm25_score,
                    vector_score=chunk.vector_score,
                )
            )

        log.debug(
            "reranker.complete",
            query=query[:50],
            input_count=len(chunks),
            output_count=len(results),
            top_score=round(results[0].score, 4) if results else None,
        )
        return results
