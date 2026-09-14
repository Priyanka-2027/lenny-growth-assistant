"""Tests for session CRUD API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    response = await client.post("/api/v1/sessions", json={"title": "Test Session"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Session"
    assert "id" in data
    assert "created_at" in data
    assert data["message_count"] == 0


@pytest.mark.asyncio
async def test_create_session_no_title(client: AsyncClient):
    response = await client.post("/api/v1/sessions", json={})
    assert response.status_code == 201
    assert response.json()["title"] is None


@pytest.mark.asyncio
async def test_list_sessions_empty(client: AsyncClient):
    response = await client.get("/api/v1/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "total" in data
    assert isinstance(data["sessions"], list)


@pytest.mark.asyncio
async def test_list_sessions_after_create(client: AsyncClient):
    await client.post("/api/v1/sessions", json={"title": "Session A"})
    await client.post("/api/v1/sessions", json={"title": "Session B"})
    response = await client.get("/api/v1/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_get_session_by_id(client: AsyncClient):
    create_resp = await client.post("/api/v1/sessions", json={"title": "Fetchable"})
    session_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["id"] == session_id
    assert response.json()["title"] == "Fetchable"


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/sessions/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient):
    create_resp = await client.post("/api/v1/sessions", json={"title": "Delete Me"})
    session_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/sessions/{session_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_session_with_metadata(client: AsyncClient):
    response = await client.post(
        "/api/v1/sessions",
        json={"title": "Meta Session", "user_metadata": {"user_id": "u123", "team": "growth"}},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_metadata"]["user_id"] == "u123"


@pytest.mark.asyncio
async def test_list_sessions_pagination(client: AsyncClient):
    for i in range(5):
        await client.post("/api/v1/sessions", json={"title": f"Session {i}"})

    response = await client.get("/api/v1/sessions?limit=2&offset=0")
    assert response.status_code == 200
    assert len(response.json()["sessions"]) <= 2
