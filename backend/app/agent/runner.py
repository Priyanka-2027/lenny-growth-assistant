"""
Agent runner — orchestrates RAG retrieval, skill routing, and LLM calls.

Skill routing:
  skill=None       → Grounded conversational RAG answer
  skill="ship30"   → Ship 30 for 30 essay
  skill="artifact_md"   → Markdown artifact
  skill="artifact_html" → HTML artifact
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.agent.llm_client import LLMMessage, get_llm_client
from app.agent.prompts import BASE_SYSTEM_PROMPT, GROUNDED_CONTEXT_TEMPLATE
from app.core.config import Settings
from app.core.logging import get_logger
from app.db.models import Message
from app.retrieval.rag import retrieve_context
from app.schemas.chat import ArtifactPayload, Source
from app.skills.artifact_skill import build_artifact_prompt
from app.skills.ship30 import SHIP30_SYSTEM_PROMPT, build_ship30_prompt

logger = get_logger(__name__)


@dataclass
class AgentResult:
    content: str
    sources: list[Source] = field(default_factory=list)
    artifact: ArtifactPayload | None = None


class AgentRunner:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._llm = get_llm_client(settings)

    def _history_to_messages(self, history: list[Message]) -> list[LLMMessage]:
        """Convert DB Message objects to LLMMessage, excluding system messages."""
        return [
            LLMMessage(role=m.role, content=m.content)
            for m in history
            if m.role in ("user", "assistant")
        ]

    async def run(
        self,
        user_message: str,
        history: list[Message],
        skill: str | None = None,
    ) -> AgentResult:
        """
        Main entry point. Routes to the correct skill or RAG pipeline.
        """
        logger.info(
            "agent_run_start",
            skill=skill or "rag",
            message_preview=user_message[:80],
        )

        if skill == "ship30":
            return await self._run_ship30(user_message, history)
        elif skill in ("artifact_md", "artifact_html"):
            artifact_type = "markdown" if skill == "artifact_md" else "html"
            return await self._run_artifact_inline(user_message, history, artifact_type)
        else:
            return await self._run_rag(user_message, history)

    # ── RAG conversational ────────────────────────────────────────────────────

    async def _run_rag(
        self,
        user_message: str,
        history: list[Message],
    ) -> AgentResult:
        context_block, sources = retrieve_context(user_message, self._settings)

        system = BASE_SYSTEM_PROMPT
        if context_block:
            system += GROUNDED_CONTEXT_TEMPLATE.format(context_block=context_block)

        messages = self._history_to_messages(history)
        messages.append(LLMMessage(role="user", content=user_message))

        content = await self._llm.complete(messages, system=system)
        return AgentResult(content=content, sources=sources)

    # ── Ship 30 for 30 ────────────────────────────────────────────────────────

    async def _run_ship30(
        self,
        user_message: str,
        history: list[Message],
    ) -> AgentResult:
        context_block, sources = retrieve_context(user_message, self._settings)
        user_prompt = build_ship30_prompt(user_message, context_block)

        messages = [LLMMessage(role="user", content=user_prompt)]
        content = await self._llm.complete(messages, system=SHIP30_SYSTEM_PROMPT)

        logger.info("ship30_essay_generated", words=len(content.split()))
        return AgentResult(content=content, sources=sources)

    # ── Inline artifact ───────────────────────────────────────────────────────

    async def _run_artifact_inline(
        self,
        user_message: str,
        history: list[Message],
        artifact_type: str,
    ) -> AgentResult:
        context_block, sources = retrieve_context(user_message, self._settings)

        # Build context from recent conversation
        history_context = "\n".join(
            f"{m.role.upper()}: {m.content[:300]}"
            for m in history[-6:]
            if m.role in ("user", "assistant")
        )

        system, user_prompt = build_artifact_prompt(
            artifact_type=artifact_type,
            title=user_message[:100],
            instructions=user_message,
            context_block=f"{context_block}\n\nCONVERSATION:\n{history_context}",
        )

        messages = [LLMMessage(role="user", content=user_prompt)]
        content = await self._llm.complete(messages, system=system)

        artifact = ArtifactPayload(
            artifact_type=artifact_type,
            title=user_message[:80],
            content=content,
        )

        logger.info("inline_artifact_generated", type=artifact_type)
        return AgentResult(content=f"Here is your {artifact_type} artifact.", sources=sources, artifact=artifact)

    # ── Standalone artifact generation (called from artifacts endpoint) ────────

    async def generate_artifact(
        self,
        artifact_type: str,
        title: str,
        instructions: str,
        history: list[Message],
    ) -> str:
        context_block, _ = retrieve_context(instructions, self._settings)

        history_context = "\n".join(
            f"{m.role.upper()}: {m.content[:300]}"
            for m in history[-6:]
            if m.role in ("user", "assistant")
        )

        system, user_prompt = build_artifact_prompt(
            artifact_type=artifact_type,
            title=title,
            instructions=instructions,
            context_block=f"{context_block}\n\nCONVERSATION:\n{history_context}",
        )

        messages = [LLMMessage(role="user", content=user_prompt)]
        content = await self._llm.complete(messages, system=system)
        logger.info("artifact_content_generated", type=artifact_type, title=title)
        return content
