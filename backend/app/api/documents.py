"""Documents API router — full implementation.

Handles file upload, ingestion triggering, document CRUD, and chunk listing.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_db
from app.core.config import get_settings
from app.rag.ingestion.pipeline import IngestionPipeline
from app.schemas.document import (
    ChunkResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents")
log = structlog.get_logger(__name__)

_ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md", "csv"}


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #


async def _run_ingestion(document_id: uuid.UUID, file_path: str, file_type: str) -> None:
    """Background task: run ingestion pipeline with its own DB session."""
    from app.core.database import SessionLocal  # noqa: PLC0415

    async with SessionLocal() as db:
        try:
            settings = get_settings()
            pipeline = IngestionPipeline(db=db, settings=settings)
            await pipeline.ingest(
                document_id=document_id,
                file_path=file_path,
                file_type=file_type,
            )
        except Exception:
            log.exception("background.ingestion.failed", document_id=str(document_id))


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentResponse,
    summary="Upload document",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload a document and enqueue it for async ingestion."""
    settings = get_settings()

    # Validate extension
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '.{ext}'. Allowed: {_ALLOWED_EXTENSIONS}",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB} MB",
        )

    # Save to disk
    doc_id = uuid.uuid4()
    upload_dir = Path(settings.UPLOAD_DIR) / str(doc_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = str(upload_dir / filename)
    with open(file_path, "wb") as fh:
        fh.write(content)

    # Persist record
    doc = await DocumentService.create_document(
        db=db,
        name=Path(filename).stem,
        original_filename=filename,
        file_path=file_path,
        file_type=ext,
        file_size=len(content),
        collection_id=collection_id,
    )

    # Launch background ingestion
    background_tasks.add_task(
        _run_ingestion, doc.id, file_path, ext
    )

    log.info("document.upload.accepted", doc_id=str(doc.id), filename=filename)
    return DocumentResponse.model_validate(doc)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents",
)
async def list_documents(
    pagination: PaginationParams = Depends(),
    collection_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    file_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """Return a paginated list of documents with optional filters."""
    items, total = await DocumentService.get_documents(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
        collection_id=collection_id,
        status=status_filter,
        file_type=file_type,
    )
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document",
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Return a single document by ID."""
    doc = await DocumentService.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document, its chunks, and its file from disk."""
    doc = await DocumentService.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove uploaded file directory
    try:
        file_dir = Path(doc.file_path).parent
        if file_dir.exists():
            shutil.rmtree(file_dir, ignore_errors=True)
    except Exception:
        log.exception("document.delete.file_error", doc_id=str(document_id))

    await DocumentService.delete_document(db, document_id)


@router.post(
    "/{document_id}/reindex",
    response_model=DocumentStatusResponse,
    summary="Re-index document",
)
async def reindex_document(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    """Re-run the ingestion pipeline for a document."""
    doc = await DocumentService.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Reset status
    doc = await DocumentService.update_document_status(db, document_id, "uploading")

    background_tasks.add_task(
        _run_ingestion, document_id, doc.file_path, doc.file_type
    )
    return DocumentStatusResponse.model_validate(doc)


@router.get(
    "/{document_id}/chunks",
    response_model=list,
    summary="List chunks",
)
async def list_document_chunks(
    document_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Return paginated chunks for a document."""
    doc = await DocumentService.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = await DocumentService.get_document_chunks(
        db, document_id, skip=pagination.skip, limit=pagination.limit
    )
    return [ChunkResponse.model_validate(c) for c in chunks]
