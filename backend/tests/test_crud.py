"""
Unit tests for database CRUD operations.
Runs against the in-memory SQLite test DB from conftest.
"""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db import crud


@pytest.mark.asyncio
async def test_create_and_get_session(db_session: AsyncSession):
    session = await crud.create_session(db_session, title="My Session")
    fetched = await crud.get_session(db_session, session.id)
    assert fetched.id == session.id
    assert fetched.title == "My Session"


@pytest.mark.asyncio
async def test_get_session_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await crud.get_session(db_session, uuid.uuid4())


@pytest.mark.asyncio
async def test_list_sessions(db_session: AsyncSession):
    await crud.create_session(db_session, title="S1")
    await crud.create_session(db_session, title="S2")
    sessions, total = await crud.list_sessions(db_session)
    assert total >= 2
    titles = [s.title for s in sessions]
    assert "S1" in titles
    assert "S2" in titles


@pytest.mark.asyncio
async def test_delete_session(db_session: AsyncSession):
    session = await crud.create_session(db_session, title="Delete Me")
    await crud.delete_session(db_session, session.id)
    with pytest.raises(NotFoundError):
        await crud.get_session(db_session, session.id)


@pytest.mark.asyncio
async def test_create_message(db_session: AsyncSession):
    session = await crud.create_session(db_session, title="Msg Session")
    msg = await crud.create_message(
        db_session,
        session_id=session.id,
        role="user",
        content="Hello world",
    )
    assert msg.content == "Hello world"
    assert msg.role == "user"
    assert msg.session_id == session.id


@pytest.mark.asyncio
async def test_create_message_with_sources(db_session: AsyncSession):
    session = await crud.create_session(db_session)
    sources = [{"title": "Ep1", "episode": "Episode 1", "relevance_score": 0.95}]
    msg = await crud.create_message(
        db_session,
        session_id=session.id,
        role="assistant",
        content="Grounded answer",
        sources=sources,
        model_used="ollama/llama3.2",
    )
    assert msg.sources == sources
    assert msg.model_used == "ollama/llama3.2"


@pytest.mark.asyncio
async def test_get_session_messages_ordered(db_session: AsyncSession):
    session = await crud.create_session(db_session, title="Order Test")
    await crud.create_message(db_session, session.id, "user", "First")
    await crud.create_message(db_session, session.id, "assistant", "Second")
    await crud.create_message(db_session, session.id, "user", "Third")

    messages = await crud.get_session_messages(db_session, session.id)
    assert len(messages) == 3
    assert messages[0].content == "First"
    assert messages[1].content == "Second"
    assert messages[2].content == "Third"


@pytest.mark.asyncio
async def test_create_artifact(db_session: AsyncSession):
    session = await crud.create_session(db_session)
    artifact = await crud.create_artifact(
        db_session,
        session_id=session.id,
        artifact_type="markdown",
        title="Test Doc",
        content="# Hello\n\nThis is a test.",
    )
    assert artifact.title == "Test Doc"
    assert artifact.artifact_type == "markdown"
    assert artifact.session_id == session.id


@pytest.mark.asyncio
async def test_list_session_artifacts(db_session: AsyncSession):
    session = await crud.create_session(db_session)
    await crud.create_artifact(db_session, session.id, "markdown", "A1", "content 1")
    await crud.create_artifact(db_session, session.id, "html", "A2", "<html></html>")

    artifacts = await crud.list_session_artifacts(db_session, session.id)
    assert len(artifacts) == 2


@pytest.mark.asyncio
async def test_create_message_invalid_session(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await crud.create_message(
            db_session,
            session_id=uuid.uuid4(),
            role="user",
            content="Orphan message",
        )
