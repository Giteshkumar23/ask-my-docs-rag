"""Integration tests for the /api/query endpoints."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestQueryAPI:
    """Integration tests for the query router."""

    async def test_submit_query_returns_501(self, async_client: AsyncClient) -> None:
        """Phase 1: query endpoint returns 501 Not Implemented."""
        response = await async_client.post(
            "/api/query",
            json={"question": "What is RAG?"},
        )
        assert response.status_code == 501

    async def test_list_queries_returns_501(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/query")
        assert response.status_code == 501

    async def test_get_query_returns_501(self, async_client: AsyncClient) -> None:
        response = await async_client.get(f"/api/query/{uuid.uuid4()}")
        assert response.status_code == 501
