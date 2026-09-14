"""
Chat endpoint — the main conversational interface.
Routes requests through the agent, persists messages, returns grounded responses.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runner import AgentRunner
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.db import crud
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Send a message to the assistant.

    - Retrieves relevant transcript context (RAG)
    - Runs the agent with optional skill routing
    - Persists user + assistant messages
    - Returns grounded response with source citations
    """
    try:
        # 1. Persist user message
        user_msg = await crud.create_message(
            db,
            session_id=body.session_id,
            role="user",
            content=body.message,
        )

        # 2. Load conversation history for context
        history = await crud.get_session_messages(db, body.session_id, limit=20)

        # 3. Run agent
        runner = AgentRunner(settings=settings)
        result = await runner.run(
            user_message=body.message,
            history=history,
            skill=body.skill,
        )

        # 4. Persist assistant message
        assistant_msg = await crud.create_message(
            db,
            session_id=body.session_id,
            role="assistant",
            content=result.content,
            sources=[s.model_dump() for s in result.sources],
            skill_used=body.skill,
            model_used=settings.active_model_name,
        )

        logger.info(
            "chat_response_generated",
            session_id=str(body.session_id),
            skill=body.skill,
            sources_count=len(result.sources),
            model=settings.active_model_name,
        )

        return ChatResponse(
            message=MessageResponse.model_validate(assistant_msg),
            sources=result.sources,
            artifact=result.artifact,
        )

    except AppError as e:
        raise to_http_exception(e)


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve message history for a session."""
    try:
        messages = await crud.get_session_messages(db, session_id)
        return [MessageResponse.model_validate(m) for m in messages]
    except AppError as e:
        raise to_http_exception(e)
