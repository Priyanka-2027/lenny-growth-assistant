"""
Transcript ingestion pipeline.

Flow:
  1. Scan transcripts/ directory for .txt and .md files
  2. Parse episode metadata from filename / file header
  3. Chunk text using langchain's RecursiveCharacterTextSplitter
  4. Embed chunks with sentence-transformers (via VectorStore)
  5. Upsert into ChromaDB with source metadata for citation

Refresh strategy: upsert by chunk ID — re-running is idempotent.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.core.exceptions import RetrievalError
from app.core.logging import get_logger
from app.retrieval.vector_store import get_vector_store

logger = get_logger(__name__)

TRANSCRIPTS_DIR = Path(__file__).parent.parent.parent / "transcripts"


def _parse_metadata(filename: str, content: str) -> dict:
    """
    Extract episode/guest metadata from filename and first 300 chars.
    Expected filename patterns:
      - lenny_ep123_guest-name.txt
      - ep123_title.txt
      - any-name.txt  → falls back to filename as title
    """
    stem = Path(filename).stem
    title = stem.replace("_", " ").replace("-", " ").title()
    episode = None

    ep_match = re.search(r"ep(\d+)", stem, re.IGNORECASE)
    if ep_match:
        episode = f"Episode {ep_match.group(1)}"

    # Try to extract guest name from "Guest: ..." in first 300 chars
    guest_match = re.search(r"(?:guest|with):\s*([^\n]+)", content[:300], re.IGNORECASE)
    guest = guest_match.group(1).strip() if guest_match else None

    return {
        "source_file": filename,
        "title": title,
        "episode": episode or title,
        "guest": guest or "",
    }


def _chunk_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def _make_chunk_id(source_file: str, chunk_index: int) -> str:
    """Stable, deterministic chunk ID for upsert idempotency."""
    raw = f"{source_file}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


async def run_ingestion(settings: Settings) -> dict:
    """
    Main ingestion entry point. Returns stats dict.
    Raises RetrievalError on failure.
    """
    if not TRANSCRIPTS_DIR.exists():
        logger.warning("transcripts_dir_missing", path=str(TRANSCRIPTS_DIR))
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        return {"transcripts_processed": 0, "chunks_indexed": 0}

    transcript_files = list(TRANSCRIPTS_DIR.glob("*.txt")) + list(TRANSCRIPTS_DIR.glob("*.md"))

    if not transcript_files:
        logger.warning("no_transcripts_found", dir=str(TRANSCRIPTS_DIR))
        return {"transcripts_processed": 0, "chunks_indexed": 0}

    try:
        store = get_vector_store(settings)
        total_chunks = 0

        for filepath in transcript_files:
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                if len(content.strip()) < 100:
                    logger.warning("transcript_too_short", file=filepath.name)
                    continue

                meta = _parse_metadata(filepath.name, content)
                chunks = _chunk_text(content, settings.chunk_size, settings.chunk_overlap)

                texts, metadatas, ids = [], [], []
                for i, chunk in enumerate(chunks):
                    chunk_id = _make_chunk_id(filepath.name, i)
                    texts.append(chunk)
                    metadatas.append({**meta, "chunk_index": i, "chunk_id": chunk_id})
                    ids.append(chunk_id)

                store.add_chunks(texts=texts, metadatas=metadatas, ids=ids)
                total_chunks += len(chunks)
                logger.info(
                    "transcript_ingested",
                    file=filepath.name,
                    chunks=len(chunks),
                )

            except Exception as exc:
                logger.error("transcript_ingestion_error", file=filepath.name, error=str(exc))
                continue

        return {
            "transcripts_processed": len(transcript_files),
            "chunks_indexed": total_chunks,
        }

    except Exception as exc:
        logger.error("ingestion_pipeline_failed", error=str(exc))
        raise RetrievalError(f"Ingestion failed: {exc}")
