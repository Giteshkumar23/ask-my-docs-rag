"""Collections API router — full implementation."""
from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_db
from app.models.collection import Collection
from app.models.document import Document
from app.schemas.collection import (
    CollectionCreate,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
)

router = APIRouter(prefix="/collections")
log = structlog.get_logger(__name__)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CollectionResponse,
    summary="Create collection",
)
async def create_collection(
    body: CollectionCreate,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Create a new document collection."""
    # Check name uniqueness
    existing = await db.execute(
        select(Collection).where(Collection.name == body.name)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Collection with name '{body.name}' already exists",
        )

    col = Collection(
        id=uuid.uuid4(),
        name=body.name,
        description=body.description,
        color=body.color,
        document_count=0,
    )
    db.add(col)
    await db.commit()
    await db.refresh(col)
    log.info("collection.created", collection_id=str(col.id), name=col.name)
    return CollectionResponse.model_validate(col)


@router.get(
    "",
    response_model=CollectionListResponse,
    summary="List collections",
)
async def list_collections(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> CollectionListResponse:
    """Return a paginated list of collections."""
    total_result = await db.execute(select(func.count()).select_from(Collection))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Collection)
        .order_by(Collection.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    items = list(result.scalars().all())

    return CollectionListResponse(
        items=[CollectionResponse.model_validate(c) for c in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Get collection",
)
async def get_collection(
    collection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Return a single collection by ID."""
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    col = result.scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return CollectionResponse.model_validate(col)


@router.put(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Update collection",
)
async def update_collection(
    collection_id: uuid.UUID,
    body: CollectionUpdate,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Update a collection's name, description, or color."""
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    col = result.scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    values = body.model_dump(exclude_none=True)
    if values:
        # Check name uniqueness if renaming
        if "name" in values and values["name"] != col.name:
            existing = await db.execute(
                select(Collection).where(Collection.name == values["name"])
            )
            if existing.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Collection name '{values['name']}' already exists",
                )
        await db.execute(
            update(Collection).where(Collection.id == collection_id).values(**values)
        )
        await db.commit()

    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    col = result.scalar_one()
    return CollectionResponse.model_validate(col)


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection",
)
async def delete_collection(
    collection_id: uuid.UUID,
    force: bool = Query(False, description="Delete even if collection has documents"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a collection; requires force=true if it has documents."""
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    col = result.scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    if col.document_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Collection has {col.document_count} documents. "
                "Pass ?force=true to delete anyway (documents will be unlinked)."
            ),
        )

    # Unlink documents (SET NULL via FK constraint, but we do it explicitly too)
    await db.execute(
        update(Document)
        .where(Document.collection_id == collection_id)
        .values(collection_id=None)
    )
    await db.execute(delete(Collection).where(Collection.id == collection_id))
    await db.commit()
    log.info("collection.deleted", collection_id=str(collection_id))


@router.post(
    "/{collection_id}/documents/{doc_id}",
    response_model=CollectionResponse,
    summary="Add document to collection",
)
async def add_document_to_collection(
    collection_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Assign a document to a collection."""
    col_result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    col = col_result.scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    doc_result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.execute(
        update(Document).where(Document.id == doc_id).values(collection_id=collection_id)
    )
    # Update count
    count_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.collection_id == collection_id)
    )
    new_count = count_result.scalar_one()
    await db.execute(
        update(Collection).where(Collection.id == collection_id).values(document_count=new_count)
    )
    await db.commit()

    col_result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    return CollectionResponse.model_validate(col_result.scalar_one())


@router.delete(
    "/{collection_id}/documents/{doc_id}",
    response_model=CollectionResponse,
    summary="Remove document from collection",
)
async def remove_document_from_collection(
    collection_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Remove a document from a collection (unlink, not delete)."""
    col_result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    col = col_result.scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    doc_result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.collection_id != collection_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document does not belong to this collection",
        )

    await db.execute(
        update(Document).where(Document.id == doc_id).values(collection_id=None)
    )
    count_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.collection_id == collection_id)
    )
    new_count = count_result.scalar_one()
    await db.execute(
        update(Collection).where(Collection.id == collection_id).values(document_count=new_count)
    )
    await db.commit()

    col_result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    return CollectionResponse.model_validate(col_result.scalar_one())
