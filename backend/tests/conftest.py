"""
Shared pytest fixtures.

Uses an in-memory SQLite database (via aiosqlite) so tests run without
a live PostgreSQL instance. The LLM is mocked throughout — we never
make real API calls in unit tests.
"""
import asyncio
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app

# ── In-memory SQLite engine for tests ─────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        # Import models to register them
        import app.db.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test transactional session — rolled back after each test."""
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTPX async client wired to the FastAPI app.
    Overrides the DB dependency with the test session.
    Mocks the LLM so no real API calls are made.
    """
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Mock the AgentRunner so tests don't need a real LLM
    with patch("app.api.routes.chat.AgentRunner") as mock_runner_cls, \
         patch("app.api.routes.artifacts.AgentRunner") as mock_art_runner_cls:

        from app.schemas.chat import ArtifactPayload, Source

        mock_result = MagicMock()
        mock_result.content = "This is a mocked assistant response grounded in transcripts."
        mock_result.sources = [
            Source(
                title="How to Find PMF",
                episode="Episode 1",
                chunk_index=0,
                relevance_score=0.92,
                excerpt="Product-market fit means the market pulls you forward.",
            )
        ]
        mock_result.artifact = None

        mock_runner = AsyncMock()
        mock_runner.run = AsyncMock(return_value=mock_result)
        mock_runner.generate_artifact = AsyncMock(
            return_value="# Test Artifact\n\nThis is generated content."
        )
        mock_runner_cls.return_value = mock_runner
        mock_art_runner_cls.return_value = mock_runner

        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://test"
        ) as ac:
            yield ac

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        app_env="test",
        llm_provider="ollama",
        ollama_model="llama3.2",
        database_url=TEST_DB_URL,
        chroma_persist_dir="/tmp/test_chroma",
        embedding_model="all-MiniLM-L6-v2",
    )
