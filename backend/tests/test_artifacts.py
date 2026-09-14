"""Tests for artifact generation and retrieval endpoints."""
import pytest
from httpx import AsyncClient


async def _create_session(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/sessions", json={"title": "Artifact Test"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_generate_markdown_artifact(client: AsyncClient):
    session_id = await _create_session(client)
    response = await client.post(
        "/api/v1/artifacts",
        json={
            "session_id": session_id,
            "artifact_type": "markdown",
            "title": "PMF Summary",
            "instructions": "Summarize product-market fit concepts",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["artifact_type"] == "markdown"
    assert data["title"] == "PMF Summary"
    assert len(data["content"]) > 0
    assert "id" in data


@pytest.mark.asyncio
async def test_generate_html_artifact(client: AsyncClient):
    session_id = await _create_session(client)
    response = await client.post(
        "/api/v1/artifacts",
        json={
            "session_id": session_id,
            "artifact_type": "html",
            "title": "Growth Dashboard",
            "instructions": "Create an HTML page summarizing growth loops",
        },
    )
    assert response.status_code == 201
    assert response.json()["artifact_type"] == "html"


@pytest.mark.asyncio
async def test_get_artifact_by_id(client: AsyncClient):
    session_id = await _create_session(client)
    create_resp = await client.post(
        "/api/v1/artifacts",
        json={
            "session_id": session_id,
            "artifact_type": "markdown",
            "title": "Fetchable Artifact",
            "instructions": "Write anything",
        },
    )
    artifact_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/artifacts/{artifact_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == artifact_id


@pytest.mark.asyncio
async def test_list_session_artifacts(client: AsyncClient):
    session_id = await _create_session(client)
    await client.post(
        "/api/v1/artifacts",
        json={"session_id": session_id, "artifact_type": "markdown", "title": "A1", "instructions": "x"},
    )
    await client.post(
        "/api/v1/artifacts",
        json={"session_id": session_id, "artifact_type": "html", "title": "A2", "instructions": "y"},
    )

    response = await client.get(f"/api/v1/artifacts/session/{session_id}")
    assert response.status_code == 200
    artifacts = response.json()
    assert len(artifacts) == 2


@pytest.mark.asyncio
async def test_invalid_artifact_type_rejected(client: AsyncClient):
    session_id = await _create_session(client)
    response = await client.post(
        "/api/v1/artifacts",
        json={
            "session_id": session_id,
            "artifact_type": "pdf",  # invalid
            "title": "Bad Type",
            "instructions": "Generate something",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_artifact_not_found(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/artifacts/{fake_id}")
    assert response.status_code == 404
