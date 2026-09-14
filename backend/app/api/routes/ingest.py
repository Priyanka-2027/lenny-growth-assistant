"""
Transcript ingestion endpoint.
Triggers loading, chunking, embedding, and indexing of transcripts into ChromaDB.
"""
from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.ingestion.pipeline import run_ingestion
from app.schemas.ingest import IngestResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=IngestResponse)
async def ingest_transcripts(
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
):
    """
    Trigger transcript ingestion.
    Loads all .txt/.md files from the transcripts/ directory,
    chunks them, embeds with sentence-transformers, and indexes in ChromaDB.
    Returns immediately — heavy work runs in the background.
    """
    try:
        result = await run_ingestion(settings=settings)
        logger.info(
            "ingestion_complete",
            transcripts=result["transcripts_processed"],
            chunks=result["chunks_indexed"],
        )
        return IngestResponse(
            status="ok",
            transcripts_processed=result["transcripts_processed"],
            chunks_indexed=result["chunks_indexed"],
            message=f"Successfully indexed {result['chunks_indexed']} chunks from "
                    f"{result['transcripts_processed']} transcripts.",
        )
    except AppError as e:
        raise to_http_exception(e)


@router.get("/status", summary="Check vector store stats")
async def ingest_status(settings: Settings = Depends(get_settings)):
    """Returns the current number of chunks in the vector store."""
    try:
        from app.retrieval.vector_store import get_vector_store
        store = get_vector_store(settings)
        count = store.collection.count()
        return {
            "collection": settings.chroma_collection_name,
            "chunk_count": count,
            "embedding_model": settings.embedding_model,
        }
    except Exception as exc:
        logger.warning("ingest_status_error", error=str(exc))
        return {"collection": settings.chroma_collection_name, "chunk_count": 0, "error": str(exc)}
