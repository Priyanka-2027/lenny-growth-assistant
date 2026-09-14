"""Pydantic schemas for standalone artifact generation."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ArtifactRequest(BaseModel):
    session_id: UUID
    artifact_type: str = Field(..., pattern="^(markdown|html)$")
    title: str = Field(..., max_length=200)
    instructions: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="What the artifact should contain/do",
    )


class ArtifactResponse(BaseModel):
    id: UUID
    session_id: UUID
    artifact_type: str
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
