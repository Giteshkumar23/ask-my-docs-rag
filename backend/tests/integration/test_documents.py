"""Integration tests for the /api/documents endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDocumentsAPI:
    """Integration tests for the documents router."""

    async def test_upload_returns_501(self, async_client: AsyncClient) -> None:
        """Phase 1: upload endpoint returns 501 Not Implemented."""
        response = await async_client.post(
            "/api/documents",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 501

    async def test_list_returns_501(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/documents")
        assert response.status_code == 501

    async def test_get_returns_501(self, async_client: AsyncClient) -> None:
        import uuid
        response = await async_client.get(f"/api/documents/{uuid.uuid4()}")
        assert response.status_code == 501

    async def test_delete_returns_501(self, async_client: AsyncClient) -> None:
        import uuid
        response = await async_client.delete(f"/api/documents/{uuid.uuid4()}")
        assert response.status_code == 501
