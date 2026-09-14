"""Tests for the chat endpoint — LLM is mocked via conftest."""
import pytest
from httpx import AsyncClient


async def _create_session(client: AsyncClient, title: str = "Chat Test") -> str:
    resp = await client.post("/api/v1/sessions", json={"title": title})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_chat_returns_assistant_message(client: AsyncClient):
    session_id = await _create_session(client)
    response = await client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "What is product-market fit?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"]["role"] == "assistant"
    assert len(data["message"]["content"]) > 0


@pytest.mark.asyncio
async def test_chat_includes_sources(client: AsyncClient):
    session_id = await _create_session(client)
    response = await client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "Explain growth loops"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)
    if data["sources"]:
        src = data["sources"][0]
        assert "title" in src
        assert "episode" in src


@pytest.mark.asyncio
async def test_chat_persists_messages(client: AsyncClient):
    session_id = await _create_session(client)
    await client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "Hello"},
    )
    history = await client.get(f"/api/v1/chat/{session_id}/messages")
    assert history.status_code == 200
    messages = history.json()
    assert len(messages) >= 2  # user + assistant
    roles = [m["role"] for m in messages]
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_chat_with_ship30_skill(client: AsyncClient):
    session_id = await _create_session(client)
    response = await client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "Write about product-market fit",
            "skill": "ship30",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"]["skill_used"] == "ship30"


@pytest.mark.asyncio
async def test_chat_invalid_session(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        "/api/v1/chat",
        json={"session_id": fake_id, "message": "Hello"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_chat_empty_message_rejected(client: AsyncClient):
    session_id = await _create_session(client)
    response = await client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_multi_turn_history(client: AsyncClient):
    session_id = await _create_session(client)
    await client.post("/api/v1/chat", json={"session_id": session_id, "message": "Turn 1"})
    await client.post("/api/v1/chat", json={"session_id": session_id, "message": "Turn 2"})

    history = await client.get(f"/api/v1/chat/{session_id}/messages")
    messages = history.json()
    # 2 user + 2 assistant = 4 messages
    assert len(messages) >= 4


@pytest.mark.asyncio
async def test_get_messages_empty_session(client: AsyncClient):
    session_id = await _create_session(client)
    response = await client.get(f"/api/v1/chat/{session_id}/messages")
    assert response.status_code == 200
    assert response.json() == []
