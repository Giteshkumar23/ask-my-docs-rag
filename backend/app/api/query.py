"""Query API router — full implementation.

Executes the full RAG pipeline: hybrid retrieval → reranking → LLM generation
→ citation validation → DB persistence.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_db
from app.core.config import get_settings
from app.models.query import Citation, Query as QueryModel, QueryResult
from app.rag.citations.parser import parse_citations
from app.rag.citations.validator import CitationValidator
from app.rag.generation.llm import LLMGenerator
from app.rag.reranking.cross_encoder import CrossEncoderReranker
from app.rag.retrieval.hybrid import HybridRetriever
from app.schemas.query import (
    CitationResponse,
    QueryListResponse,
    QueryRequest,
    QueryResponse,
)

router = APIRouter(prefix="/query")
log = structlog.get_logger(__name__)


def _determine_confidence(chunks: list, answer: str) -> str:
    """Heuristic confidence label based on top reranker score and answer text."""
    if "couldn't find enough evidence" in answer.lower():
        return "insufficient"
    if not chunks:
        return "insufficient"
    top_score = chunks[0].score
    if top_score > 0.7:
        return "high"
    if top_score > 0.4:
        return "moderate"
    return "low"


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=QueryResponse,
    summary="Submit query",
)
async def submit_query(
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Run the full RAG pipeline and return a cited answer."""
    settings = get_settings()
    total_start = time.perf_counter()

    # 1. Create Query record
    query_record = QueryModel(
        id=uuid.uuid4(),
        question=body.question,
        collection_id=body.collection_id,
        status="processing",
    )
    db.add(query_record)
    await db.commit()
    await db.refresh(query_record)

    try:
        # 2. Hybrid retrieval
        retrieval_start = time.perf_counter()
        hybrid = HybridRetriever(db=db, settings=settings)
        top_k_retrieval = settings.TOP_K_RETRIEVAL
        retrieved_chunks, retrieval_meta = await hybrid.retrieve(
            query=body.question,
            top_k=top_k_retrieval,
            collection_id=body.collection_id,
        )
        retrieval_time = time.perf_counter() - retrieval_start

        # 3. Cross-encoder reranking
        reranking_start = time.perf_counter()
        top_k_final = body.top_k or settings.TOP_K_FINAL
        reranker = CrossEncoderReranker(model_name=settings.RERANKER_MODEL)
        reranked_chunks = reranker.rerank(
            query=body.question,
            chunks=retrieved_chunks,
            top_k=top_k_final,
        )
        reranking_time = time.perf_counter() - reranking_start

        # 4. LLM generation
        generation_start = time.perf_counter()
        generator = LLMGenerator(settings=settings)
        gen_result = await generator.generate(
            query=body.question,
            chunks=reranked_chunks,
        )
        generation_time = time.perf_counter() - generation_start

        # 5. Parse and validate citations
        validator = CitationValidator()
        validation = validator.validate(gen_result.answer, reranked_chunks)

        # 6. Determine confidence
        confidence = _determine_confidence(reranked_chunks, gen_result.answer)

        total_time = time.perf_counter() - total_start

        # 7. Save QueryResults (one row per retrieved chunk)
        for rank, chunk in enumerate(reranked_chunks, start=1):
            qr = QueryResult(
                id=uuid.uuid4(),
                query_id=query_record.id,
                chunk_id=chunk.chunk_id,
                rank=rank,
                bm25_score=chunk.bm25_score,
                vector_score=chunk.vector_score,
                reranker_score=chunk.score,
                fusion_score=chunk.score,
                used_in_answer=rank in validation.cited_indices,
            )
            db.add(qr)

        # 8. Save Citations
        cited_numbers = parse_citations(gen_result.answer)
        for n in cited_numbers:
            idx = n - 1  # 0-based
            if 0 <= idx < len(reranked_chunks):
                chunk = reranked_chunks[idx]
                cit = Citation(
                    id=uuid.uuid4(),
                    query_id=query_record.id,
                    chunk_id=chunk.chunk_id,
                    citation_number=n,
                    is_valid=n in validation.cited_indices,
                )
                db.add(cit)

        # 9. Update Query record
        from sqlalchemy import update  # noqa: PLC0415
        await db.execute(
            update(QueryModel)
            .where(QueryModel.id == query_record.id)
            .values(
                answer=gen_result.answer,
                status="completed",
                confidence=confidence,
                retrieval_time=retrieval_time,
                reranking_time=reranking_time,
                generation_time=generation_time,
                total_time=total_time,
                num_chunks_retrieved=len(retrieved_chunks),
            )
        )
        await db.commit()

        # Build citations for response
        citation_responses: List[CitationResponse] = []
        for n in sorted(cited_numbers):
            idx = n - 1
            if 0 <= idx < len(reranked_chunks):
                chunk = reranked_chunks[idx]
                citation_responses.append(
                    CitationResponse(
                        citation_number=n,
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        document_name=chunk.document_name,
                        page_number=chunk.page_number,
                        section=chunk.section,
                        text_snippet=chunk.text[:300],
                        is_valid=n in validation.cited_indices,
                    )
                )

        return QueryResponse(
            id=query_record.id,
            question=body.question,
            answer=gen_result.answer,
            citations=citation_responses,
            confidence=confidence,
            retrieval_time=retrieval_time,
            reranking_time=reranking_time,
            generation_time=generation_time,
            total_time=total_time,
            num_chunks_retrieved=len(retrieved_chunks),
            status="completed",
            created_at=query_record.created_at,
        )

    except Exception as exc:  # noqa: BLE001
        log.exception(
            "query.pipeline.failed",
            query_id=str(query_record.id),
            error=str(exc),
            error_type=type(exc).__name__,
        )

        print("\n" + "=" * 80)
        print("QUERY PIPELINE ERROR")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", str(exc))
        import traceback
        traceback.print_exc()
        print("=" * 80 + "\n")
        from sqlalchemy import update  # noqa: PLC0415
        await db.execute(
            update(QueryModel)
            .where(QueryModel.id == query_record.id)
            .values(status="failed", error_message=str(exc)[:2048])
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query pipeline failed: {exc}",
        )


@router.get(
    "",
    response_model=QueryListResponse,
    summary="Query history",
)
async def list_queries(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> QueryListResponse:
    """Return paginated query history."""
    count_result = await db.execute(select(func.count()).select_from(QueryModel))
    total = count_result.scalar_one()

    result = await db.execute(
        select(QueryModel)
        .order_by(QueryModel.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    items = list(result.scalars().all())

    return QueryListResponse(
        items=[
            QueryResponse(
                id=q.id,
                question=q.question,
                answer=q.answer,
                citations=[],
                confidence=q.confidence,
                retrieval_time=q.retrieval_time,
                reranking_time=q.reranking_time,
                generation_time=q.generation_time,
                total_time=q.total_time,
                num_chunks_retrieved=q.num_chunks_retrieved,
                status=q.status,
                error_message=q.error_message,
                created_at=q.created_at,
            )
            for q in items
        ],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{query_id}",
    response_model=QueryResponse,
    summary="Get query",
)
async def get_query(
    query_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Return a single query with its citations."""
    result = await db.execute(
        select(QueryModel).where(QueryModel.id == query_id)
    )
    query_record = result.scalar_one_or_none()
    if query_record is None:
        raise HTTPException(status_code=404, detail="Query not found")

    # Load citations
    cit_result = await db.execute(
        select(Citation).where(Citation.query_id == query_id)
    )
    citations_db = cit_result.scalars().all()

    # Build citation responses (need chunk + document details)
    citation_responses: List[CitationResponse] = []
    for cit in citations_db:
        from app.models.chunk import DocumentChunk  # noqa: PLC0415
        from app.models.document import Document  # noqa: PLC0415
        chunk_result = await db.execute(
            select(DocumentChunk, Document.name.label("doc_name"))
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.id == cit.chunk_id)
        )
        row = chunk_result.first()
        if row:
            chunk, doc_name = row
            citation_responses.append(
                CitationResponse(
                    citation_number=cit.citation_number,
                    chunk_id=cit.chunk_id,
                    document_id=chunk.document_id,
                    document_name=doc_name,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    text_snippet=chunk.text[:300],
                    is_valid=cit.is_valid,
                )
            )

    citation_responses.sort(key=lambda c: c.citation_number)

    return QueryResponse(
        id=query_record.id,
        question=query_record.question,
        answer=query_record.answer,
        citations=citation_responses,
        confidence=query_record.confidence,
        retrieval_time=query_record.retrieval_time,
        reranking_time=query_record.reranking_time,
        generation_time=query_record.generation_time,
        total_time=query_record.total_time,
        num_chunks_retrieved=query_record.num_chunks_retrieved,
        status=query_record.status,
        error_message=query_record.error_message,
        created_at=query_record.created_at,
    )
