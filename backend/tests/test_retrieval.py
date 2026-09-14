"""
Tests for the RAG retrieval and ingestion pipeline.
Uses a temporary ChromaDB directory — no persistent state between tests.
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    """Settings pointing at temp dirs so tests don't pollute real chroma_db."""
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    (transcripts_dir / "ep001_test.txt").write_text(
        "Episode: Test Episode\nGuest: Test Guest\n\n"
        "Lenny: Product-market fit is about finding a market that wants your product. "
        "The key signals are retention curves flattening and organic word-of-mouth growth. "
        "Founders who find PMF fastest are those who listen obsessively to their users. "
        "They narrow their focus before expanding. Depth before breadth is the mantra.\n\n"
        "Growth loops compound over time unlike traditional funnels. "
        "The best products have embedded growth mechanisms. "
        "Activation requires finding the aha moment through data analysis.\n"
    )
    return Settings(
        app_env="test",
        llm_provider="ollama",
        database_url="sqlite+aiosqlite:///:memory:",
        chroma_persist_dir=str(tmp_path / "chroma"),
        chroma_collection_name="test_collection",
        embedding_model="all-MiniLM-L6-v2",
        retrieval_top_k=3,
        chunk_size=200,
        chunk_overlap=20,
    )


class TestIngestionPipeline:
    @pytest.mark.asyncio
    async def test_ingestion_processes_transcripts(self, tmp_settings, monkeypatch):
        """Pipeline reads transcripts and indexes chunks into ChromaDB."""
        import app.ingestion.pipeline as pipeline_mod
        monkeypatch.setattr(
            pipeline_mod,
            "TRANSCRIPTS_DIR",
            Path(tmp_settings.chroma_persist_dir).parent / "transcripts",
        )

        from app.ingestion.pipeline import run_ingestion
        result = await run_ingestion(settings=tmp_settings)

        assert result["transcripts_processed"] == 1
        assert result["chunks_indexed"] > 0

    @pytest.mark.asyncio
    async def test_ingestion_empty_dir_returns_zero(self, tmp_settings, monkeypatch, tmp_path):
        """Empty transcripts directory returns zeros gracefully."""
        empty_dir = tmp_path / "empty_transcripts"
        empty_dir.mkdir()

        import app.ingestion.pipeline as pipeline_mod
        monkeypatch.setattr(pipeline_mod, "TRANSCRIPTS_DIR", empty_dir)

        from app.ingestion.pipeline import run_ingestion
        result = await run_ingestion(settings=tmp_settings)

        assert result["transcripts_processed"] == 0
        assert result["chunks_indexed"] == 0

    @pytest.mark.asyncio
    async def test_ingestion_idempotent(self, tmp_settings, monkeypatch, tmp_path):
        """Running ingestion twice produces the same chunk count (upsert, not append)."""
        transcripts_dir = tmp_path / "transcripts"
        transcripts_dir.mkdir()
        (transcripts_dir / "ep001.txt").write_text(
            "Episode: Idempotent Test\n\nSome content about product strategy and growth loops.\n"
        )

        import app.ingestion.pipeline as pipeline_mod
        monkeypatch.setattr(pipeline_mod, "TRANSCRIPTS_DIR", transcripts_dir)

        from app.ingestion.pipeline import run_ingestion
        result1 = await run_ingestion(settings=tmp_settings)
        result2 = await run_ingestion(settings=tmp_settings)

        assert result1["chunks_indexed"] == result2["chunks_indexed"]


class TestRAGRetrieval:
    def test_retrieve_returns_sources(self, tmp_settings, monkeypatch, tmp_path):
        """After ingestion, retrieval returns relevant chunks with sources."""
        from app.retrieval.vector_store import VectorStore

        # Directly add chunks without ingestion pipeline
        store = VectorStore(tmp_settings)
        store.add_chunks(
            texts=[
                "Product-market fit is when the market pulls you forward.",
                "Growth loops compound unlike traditional marketing funnels.",
                "Retention curves that flatten indicate early PMF signal.",
            ],
            metadatas=[
                {"source_file": "ep001.txt", "title": "PMF Episode", "episode": "Episode 1", "chunk_index": 0, "chunk_id": "abc001"},
                {"source_file": "ep002.txt", "title": "Growth Episode", "episode": "Episode 2", "chunk_index": 0, "chunk_id": "abc002"},
                {"source_file": "ep001.txt", "title": "PMF Episode", "episode": "Episode 1", "chunk_index": 1, "chunk_id": "abc003"},
            ],
            ids=["abc001", "abc002", "abc003"],
        )

        from app.retrieval.rag import retrieve_context
        context_block, sources = retrieve_context("product-market fit", tmp_settings)

        assert len(sources) > 0
        assert any("PMF" in s.title or "pmf" in (s.episode or "").lower() or "Episode 1" in (s.episode or "") for s in sources)
        assert len(context_block) > 0

    def test_retrieve_empty_store_returns_empty(self, tmp_settings):
        """Empty vector store returns empty context without crashing."""
        from app.retrieval.rag import retrieve_context
        # Use fresh settings pointing to a fresh temp dir
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            fresh_settings = Settings(
                app_env="test",
                llm_provider="ollama",
                database_url="sqlite+aiosqlite:///:memory:",
                chroma_persist_dir=tmpdir + "/chroma",
                chroma_collection_name="empty_test",
                embedding_model="all-MiniLM-L6-v2",
            )
            context_block, sources = retrieve_context("anything", fresh_settings)
            assert context_block == ""
            assert sources == []

    def test_chunk_metadata_preserved(self, tmp_settings):
        """Source metadata (title, episode, chunk_index) is preserved through retrieval."""
        from app.retrieval.vector_store import VectorStore

        store = VectorStore(tmp_settings)
        store.add_chunks(
            texts=["Onboarding is the first experience of core product value."],
            metadatas=[{
                "source_file": "ep003.txt",
                "title": "Onboarding Episode",
                "episode": "Episode 3",
                "chunk_index": 2,
                "chunk_id": "meta001",
            }],
            ids=["meta001"],
        )

        chunks = store.query("onboarding user activation", top_k=1)
        assert len(chunks) == 1
        meta = chunks[0]["metadata"]
        assert meta["episode"] == "Episode 3"
        assert meta["chunk_index"] == 2
        assert "score" in chunks[0]
