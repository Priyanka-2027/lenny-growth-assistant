"""Session management endpoints."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, to_http_exception
from app.db import crud
from app.db.session import get_db
from app.schemas.session import SessionCreate, SessionListResponse, SessionResponse

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Start a new independent chat session."""
    try:
        session = await crud.create_session(
            db, title=body.title, user_metadata=body.user_metadata
        )
        return SessionResponse.model_validate(session)
    except AppError as e:
        raise to_http_exception(e)


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all sessions, most recently active first."""
    try:
        sessions, total = await crud.list_sessions(db, limit=limit, offset=offset)
        return SessionListResponse(
            sessions=[SessionResponse.model_validate(s) for s in sessions],
            total=total,
        )
    except AppError as e:
        raise to_http_exception(e)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single session by ID."""
    try:
        session = await crud.get_session(db, session_id)
        return SessionResponse.model_validate(session)
    except AppError as e:
        raise to_http_exception(e)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a session and all its messages/artifacts."""
    try:
        await crud.delete_session(db, session_id)
    except AppError as e:
        raise to_http_exception(e)
