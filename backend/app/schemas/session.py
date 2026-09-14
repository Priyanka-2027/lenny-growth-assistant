"""Pydantic schemas for chat sessions."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str | None = Field(None, max_length=200, description="Optional session title")
    user_metadata: dict | None = Field(None, description="Arbitrary caller metadata")


class SessionResponse(BaseModel):
    id: UUID
    title: str | None
    user_metadata: dict | None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
