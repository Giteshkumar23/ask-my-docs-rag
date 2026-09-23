"""Evaluation runner — full implementation.

Runs the full RAG pipeline for each question in a dataset, computes
retrieval and generation metrics, and persists per-question results plus
aggregated EvaluationRun metrics.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.evaluation import metrics as m
from app.models.evaluation import EvaluationResult, EvaluationRun
from app.rag.citations.parser import parse_citations
from app.rag.generation.llm import LLMGenerator
from app.rag.reranking.cross_encoder import CrossEncoderReranker
from app.rag.retrieval.hybrid import HybridRetriever

log = structlog.get_logger(__name__)


@dataclass
class EvalQuestion:
    """A single evaluation question with ground-truth."""

    question: str
    expected_answer: str
    expected_sources: List[str]  # list of document names or chunk IDs


class EvaluationRunner:
    """Orchestrates a full evaluation run against a question dataset.

    Parameters
    ----------
    db:
        An open :class:`AsyncSession`.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def run_evaluation(
        self,
        run_id: uuid.UUID,
        dataset: List[Dict[str, Any]],
    ) -> None:
        """Run the RAG pipeline for every question and persist results.

        If *dataset* is empty, the run is marked complete immediately with
        zero questions (caller can later supply data via a different path).
        """
        settings = get_settings()

        if not dataset:
            await self.db.execute(
                update(EvaluationRun)
                .where(EvaluationRun.id == run_id)
                .values(num_questions=0, passed=True)
            )
            await self.db.commit()
            return

        questions = [
            EvalQuestion(
                question=row.get("question", ""),
                expected_answer=row.get("expected_answer", ""),
                expected_sources=row.get("expected_sources", []),
            )
            for row in dataset
        ]

        # Per-question metric accumulators
        recalls: List[float] = []
        precisions: List[float] = []
        mrrs: List[float] = []
        hit_rates: List[float] = []
        faithfulnesses: List[float] = []
        relevances: List[float] = []
        citation_scores: List[float] = []
        retrieval_latencies: List[float] = []
        reranking_latencies: List[float] = []
        generation_latencies: List[float] = []
        total_latencies: List[float] = []

        for question in questions:
            total_start = time.perf_counter()
            generated_answer = ""
            retrieved_source_names: List[str] = []
            faithfulness = 0.0
            relevance_score = 0.0
            citation_score = 0.0
            retrieval_recall = 0.0

            try:
                # Retrieval
                ret_start = time.perf_counter()
                hybrid = HybridRetriever(db=self.db, settings=settings)
                retrieved_chunks, _ = await hybrid.retrieve(
                    query=question.question,
                    top_k=settings.TOP_K_RETRIEVAL,
                )
                retrieval_lat = time.perf_counter() - ret_start

                # Reranking
                rank_start = time.perf_counter()
                reranker = CrossEncoderReranker(model_name=settings.RERANKER_MODEL)
                reranked = reranker.rerank(
                    query=question.question,
                    chunks=retrieved_chunks,
                    top_k=settings.TOP_K_FINAL,
                )
                reranking_lat = time.perf_counter() - rank_start

                # Generation
                gen_start = time.perf_counter()
                generator = LLMGenerator(settings=settings)
                gen_result = await generator.generate(
                    query=question.question,
                    chunks=reranked,
                )
                generation_lat = time.perf_counter() - gen_start

                generated_answer = gen_result.answer
                retrieved_source_names = list({c.document_name for c in retrieved_chunks})
                total_lat = time.perf_counter() - total_start

                # Retrieval metrics (source-name based)
                relevant_set = set(question.expected_sources)
                retrieved_list = [c.document_name for c in retrieved_chunks]

                retrieval_recall = m.recall_at_k(retrieved_list, list(relevant_set), k=5)
                prec = m.precision_at_k(retrieved_list, list(relevant_set), k=5)
                mrr_val = m.mean_reciprocal_rank(retrieved_list, list(relevant_set))
                hr = m.hit_rate(retrieved_list, list(relevant_set), k=5)

                # Generation metrics (heuristic)
                chunk_texts = [c.text for c in reranked]
                faithfulness = m.compute_faithfulness(generated_answer, chunk_texts)
                relevance_score = m.compute_answer_relevance(question.question, generated_answer)

                # Citation score
                cited_nums = parse_citations(generated_answer)
                citation_score = m.citation_accuracy_by_index(cited_nums, len(reranked))

                # Accumulate
                recalls.append(retrieval_recall)
                precisions.append(prec)
                mrrs.append(mrr_val)
                hit_rates.append(hr)
                faithfulnesses.append(faithfulness)
                relevances.append(relevance_score)
                citation_scores.append(citation_score)
                retrieval_latencies.append(retrieval_lat)
                reranking_latencies.append(reranking_lat)
                generation_latencies.append(generation_lat)
                total_latencies.append(total_lat)

            except Exception:  # noqa: BLE001
                log.exception(
                    "evaluation.question.failed", question=question.question[:80]
                )
                total_lat = time.perf_counter() - total_start
                total_latencies.append(total_lat)

            # Persist per-question result
            result_row = EvaluationResult(
                id=uuid.uuid4(),
                run_id=run_id,
                question=question.question,
                expected_answer=question.expected_answer,
                generated_answer=generated_answer,
                expected_sources={"sources": question.expected_sources},
                retrieved_sources={"sources": retrieved_source_names},
                faithfulness_score=faithfulness,
                relevance_score=relevance_score,
                citation_score=citation_score,
                retrieval_recall=retrieval_recall,
            )
            self.db.add(result_row)
            await self.db.commit()

        # Aggregate and update the run
        def _avg(lst: List[float]) -> Optional[float]:
            return sum(lst) / len(lst) if lst else None

        await self.db.execute(
            update(EvaluationRun)
            .where(EvaluationRun.id == run_id)
            .values(
                num_questions=len(questions),
                recall_at_5=_avg(recalls),
                precision_at_5=_avg(precisions),
                mrr=_avg(mrrs),
                hit_rate=_avg(hit_rates),
                faithfulness=_avg(faithfulnesses),
                answer_relevance=_avg(relevances),
                citation_accuracy=_avg(citation_scores),
                avg_retrieval_latency=_avg(retrieval_latencies),
                avg_reranking_latency=_avg(reranking_latencies),
                avg_generation_latency=_avg(generation_latencies),
                avg_total_latency=_avg(total_latencies),
                passed=((_avg(recalls) or 0.0) >= 0.5),
            )
        )
        await self.db.commit()
        log.info(
            "evaluation.complete",
            run_id=str(run_id),
            num_questions=len(questions),
            recall=_avg(recalls),
        )
