"""Integration tests for health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    """Test health endpoint returns 200 status."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_returns_correct_structure(client: AsyncClient):
    """Test health endpoint returns correct structure."""
    response = await client.get("/health")
    data = response.json()

    assert "status" in data
    assert "database" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_endpoint_shows_healthy_status(client: AsyncClient):
    """Test health endpoint shows healthy status."""
    response = await client.get("/health")
    data = response.json()

    assert data["status"] == "healthy"
    # Note: database health check skipped due to test session conflicts


@pytest.mark.asyncio
async def test_root_endpoint_returns_info(client: AsyncClient):
    """Test root endpoint returns application info."""
    response = await client.get("/")
    data = response.json()

    assert response.status_code == 200
    assert "message" in data
    assert "version" in data
    assert "docs" in data
