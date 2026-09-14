"""
CRUD helpers — thin wrappers over SQLAlchemy queries.
All functions take an AsyncSession and return ORM objects.
"""
import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DatabaseError, NotFoundError
from app.core.logging import get_logger
from app.db.models import Artifact, Message, Session

logger = get_logger(__name__)


# ── Sessions ─────────────────────────────────────────────────────────────────

async def create_session(
    db: AsyncSession,
    title: str | None = None,
    user_metadata: dict | None = None,
) -> Session:
    session = Session(title=title, user_metadata=user_metadata)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    logger.info("session_created", session_id=str(session.id))
    return session


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Session:
    result = await db.execute(
        select(Session)
        .options(selectinload(Session.messages))
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError(f"Session {session_id} not found.")
    return session


async def list_sessions(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> tuple[list[Session], int]:
    count_result = await db.execute(select(func.count()).select_from(Session))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Session)
        .options(selectinload(Session.messages))
        .order_by(Session.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()
    return list(sessions), total


async def delete_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    session = await get_session(db, session_id)
    await db.delete(session)
    logger.info("session_deleted", session_id=str(session_id))


# ── Messages ──────────────────────────────────────────────────────────────────

async def create_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: str,
    content: str,
    sources: list | None = None,
    skill_used: str | None = None,
    model_used: str | None = None,
) -> Message:
    # Verify session exists
    await get_session(db, session_id)

    message = Message(
        session_id=session_id,
        role=role,
        content=content,
        sources=sources,
        skill_used=skill_used,
        model_used=model_used,
    )
    db.add(message)

    # Touch session updated_at
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(updated_at=func.now())
    )

    await db.flush()
    await db.refresh(message)
    return message


async def get_session_messages(
    db: AsyncSession, session_id: uuid.UUID, limit: int = 50
) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ── Artifacts ─────────────────────────────────────────────────────────────────

async def create_artifact(
    db: AsyncSession,
    session_id: uuid.UUID,
    artifact_type: str,
    title: str,
    content: str,
) -> Artifact:
    await get_session(db, session_id)

    artifact = Artifact(
        session_id=session_id,
        artifact_type=artifact_type,
        title=title,
        content=content,
    )
    db.add(artifact)
    await db.flush()
    await db.refresh(artifact)
    logger.info("artifact_created", artifact_id=str(artifact.id), type=artifact_type)
    return artifact


async def get_artifact(db: AsyncSession, artifact_id: uuid.UUID) -> Artifact:
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id)
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise NotFoundError(f"Artifact {artifact_id} not found.")
    return artifact


async def list_session_artifacts(
    db: AsyncSession, session_id: uuid.UUID
) -> list[Artifact]:
    result = await db.execute(
        select(Artifact)
        .where(Artifact.session_id == session_id)
        .order_by(Artifact.created_at.desc())
    )
    return list(result.scalars().all())
