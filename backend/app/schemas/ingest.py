"""Pydantic schemas for transcript ingestion."""
from pydantic import BaseModel


class IngestResponse(BaseModel):
    status: str
    transcripts_processed: int
    chunks_indexed: int
    message: str
