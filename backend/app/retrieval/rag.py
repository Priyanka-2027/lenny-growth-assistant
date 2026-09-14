"""
RAG (Retrieval-Augmented Generation) helper.
Retrieves relevant transcript chunks and formats them as context for the LLM.
"""
from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.retrieval.vector_store import get_vector_store
from app.schemas.chat import Source

logger = get_logger(__name__)


def retrieve_context(query: str, settings: Settings) -> tuple[str, list[Source]]:
    """
    Retrieve top-k transcript chunks for a query.

    Returns:
        context_block: Formatted string to inject into the LLM system prompt.
        sources: List of Source objects for citation in the response.
    """
    try:
        store = get_vector_store(settings)

        if store.collection.count() == 0:
            logger.warning("vector_store_empty", query=query[:60])
            return "", []

        chunks = store.query(query, top_k=settings.retrieval_top_k)

        if not chunks:
            return "", []

        sources = []
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            meta = chunk["metadata"]
            score = chunk["score"]

            source = Source(
                title=meta.get("title", "Unknown"),
                episode=meta.get("episode"),
                chunk_index=meta.get("chunk_index"),
                relevance_score=score,
                excerpt=chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
            )
            sources.append(source)

            context_parts.append(
                f"[Source {i}: {meta.get('title', 'Unknown')} — {meta.get('episode', '')}]\n"
                f"{chunk['text']}\n"
            )

        context_block = (
            "RELEVANT TRANSCRIPT EXCERPTS:\n"
            + "─" * 60 + "\n"
            + "\n".join(context_parts)
            + "─" * 60
        )

        logger.info(
            "context_retrieved",
            query=query[:60],
            chunks=len(chunks),
            top_score=chunks[0]["score"] if chunks else 0,
        )

        return context_block, sources

    except Exception as exc:
        logger.error("retrieval_failed", error=str(exc))
        return "", []
