"""
Database models for sessions, messages, and artifacts.

Schema:
  sessions  ──< messages
  sessions  ──< artifacts
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk


class Session(Base, TimestampMixin):
    """A single chat session with independent context."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan", lazy="select"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact", back_populates="session", cascade="all, delete-orphan", lazy="select"
    )

    @property
    def message_count(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return f"<Session id={self.id} title={self.title!r}>"


class Message(Base, TimestampMixin):
    """A single turn in a conversation (user or assistant)."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user|assistant|system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Grounding metadata
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)
    skill_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} session={self.session_id}>"


class Artifact(Base, TimestampMixin):
    """A generated Markdown or HTML artifact attached to a session."""

    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(String(20), nullable=False)  # markdown|html
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["Session"] = relationship("Session", back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<Artifact id={self.id} type={self.artifact_type} title={self.title!r}>"
