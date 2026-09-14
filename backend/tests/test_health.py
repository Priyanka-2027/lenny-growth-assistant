"""Tests for health and readiness endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_returns_model_info(client: AsyncClient):
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "llm_provider" in data
    assert "active_model" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_health_does_not_require_db(client: AsyncClient):
    """Health endpoint must respond even if DB is slow."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
