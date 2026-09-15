"""
ChromaDB vector store wrapper.
Uses sentence-transformers for local embeddings — no API key required.
"""
from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._embedding_model = SentenceTransformer(settings.embedding_model)
        self.collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "vector_store_ready",
            collection=settings.chroma_collection_name,
            chunk_count=self.collection.count(),
        )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return self._embedding_model.encode(texts, normalize_embeddings=True).tolist()

    def add_chunks(
        self,
        texts: list[str],
        metadatas: list[dict],
        ids: list[str],
    ) -> None:
        """Add a batch of chunks to the collection."""
        embeddings = self._embed(texts)
        self.collection.upsert(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info("chunks_added", count=len(texts))

    def query(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retrieve top-k chunks relevant to query_text.
        Returns list of dicts: {text, metadata, score, id}
        """
        query_embedding = self._embed([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, max(self.collection.count(), 1)),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for doc, meta, dist, cid in zip(docs, metas, distances, ids):
            # cosine distance → similarity score (1 = identical)
            score = round(1 - dist, 4)
            chunks.append({"text": doc, "metadata": meta, "score": score, "id": cid})

        logger.debug("retrieval_results", query=query_text[:60], count=len(chunks))
        return chunks

    def reset(self) -> None:
        """Delete and recreate the collection (use for re-ingestion)."""
        self._client.delete_collection(self._settings.chroma_collection_name)
        self.collection = self._client.get_or_create_collection(
            name=self._settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning("vector_store_reset")


_vector_store_instance: VectorStore | None = None


def get_vector_store(settings: Settings) -> VectorStore:
    """Singleton vector store — shared across all requests."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(settings)
    return _vector_store_instance