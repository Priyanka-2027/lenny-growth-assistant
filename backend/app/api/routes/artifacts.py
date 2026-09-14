"""Artifact generation and retrieval endpoints."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runner import AgentRunner
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.db import crud
from app.db.session import get_db
from app.schemas.artifact import ArtifactRequest, ArtifactResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ArtifactResponse, status_code=201)
async def generate_artifact(
    body: ArtifactRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Generate a Markdown or HTML artifact based on the conversation context.
    The artifact is persisted and returned for rendering in the viewer.
    """
    try:
        # Load session history for context
        history = await crud.get_session_messages(db, body.session_id, limit=20)

        runner = AgentRunner(settings=settings)
        content = await runner.generate_artifact(
            artifact_type=body.artifact_type,
            title=body.title,
            instructions=body.instructions,
            history=history,
        )

        artifact = await crud.create_artifact(
            db,
            session_id=body.session_id,
            artifact_type=body.artifact_type,
            title=body.title,
            content=content,
        )

        logger.info(
            "artifact_generated",
            artifact_id=str(artifact.id),
            type=body.artifact_type,
            session_id=str(body.session_id),
        )

        return ArtifactResponse.model_validate(artifact)

    except AppError as e:
        raise to_http_exception(e)


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch a previously generated artifact by ID."""
    try:
        artifact = await crud.get_artifact(db, artifact_id)
        return ArtifactResponse.model_validate(artifact)
    except AppError as e:
        raise to_http_exception(e)


@router.get("/session/{session_id}", response_model=list[ArtifactResponse])
async def list_session_artifacts(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all artifacts for a session."""
    try:
        artifacts = await crud.list_session_artifacts(db, session_id)
        return [ArtifactResponse.model_validate(a) for a in artifacts]
    except AppError as e:
        raise to_http_exception(e)
