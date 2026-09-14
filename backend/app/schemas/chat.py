"""Pydantic schemas for chat messages and agent responses."""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Role(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Source(BaseModel):
    """A transcript source cited in an answer."""
    title: str
    episode: str | None = None
    chunk_index: int | None = None
    relevance_score: float | None = None
    excerpt: str | None = None


class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(..., min_length=1, max_length=8000)
    skill: str | None = Field(
        None,
        description="Optional skill to invoke: 'ship30' | 'artifact_md' | 'artifact_html'",
    )


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: Role
    content: str
    sources: list[Source] = []
    skill_used: str | None = None
    model_used: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    message: MessageResponse
    sources: list[Source] = []
    artifact: "ArtifactPayload | None" = None


class ArtifactPayload(BaseModel):
    """Inline artifact returned alongside a chat response."""
    artifact_type: str  # "markdown" | "html"
    title: str
    content: str
