"""
LLM client abstraction layer.
Switch providers via LLM_PROVIDER env var — no application code changes needed.

Supported: anthropic | ollama | openai
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.exceptions import LLMTimeoutError, LLMUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Message type ──────────────────────────────────────────────────────────────

class LLMMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


# ── Base interface ────────────────────────────────────────────────────────────

class BaseLLMClient:
    """Common interface for all LLM providers."""

    async def complete(self, messages: list[LLMMessage], system: str = "") -> str:
        raise NotImplementedError

    async def stream(
        self, messages: list[LLMMessage], system: str = ""
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError
        yield  # make it a generator


# ── Anthropic ─────────────────────────────────────────────────────────────────

class AnthropicClient(BaseLLMClient):
    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise LLMUnavailableError(
                "ANTHROPIC_API_KEY is not set. Set it in .env or switch LLM_PROVIDER."
            )
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        self._timeout = settings.llm_timeout_seconds

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(self, messages: list[LLMMessage], system: str = "") -> str:
        try:
            response = await asyncio.wait_for(
                self._client.messages.create(
                    model=self._model,
                    max_tokens=4096,
                    system=system or "You are a helpful assistant.",
                    messages=[m.to_dict() for m in messages],
                ),
                timeout=self._timeout,
            )
            return response.content[0].text
        except asyncio.TimeoutError:
            raise LLMTimeoutError("Anthropic request timed out.")
        except Exception as exc:
            logger.error("anthropic_error", error=str(exc))
            raise LLMUnavailableError(f"Anthropic error: {exc}")

    async def stream(
        self, messages: list[LLMMessage], system: str = ""
    ) -> AsyncGenerator[str, None]:
        async with self._client.messages.stream(
            model=self._model,
            max_tokens=4096,
            system=system or "You are a helpful assistant.",
            messages=[m.to_dict() for m in messages],
        ) as stream:
            async for text in stream.text_stream:
                yield text


# ── Ollama ────────────────────────────────────────────────────────────────────

class OllamaClient(BaseLLMClient):
    def __init__(self, settings: Settings):
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._timeout = settings.llm_timeout_seconds

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def complete(self, messages: list[LLMMessage], system: str = "") -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": "system", "content": system}] + [m.to_dict() for m in messages]
            if system
            else [m.to_dict() for m in messages],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/api/chat", json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
        except httpx.ConnectError:
            raise LLMUnavailableError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )
        except httpx.TimeoutException:
            raise LLMTimeoutError("Ollama request timed out.")
        except Exception as exc:
            logger.error("ollama_error", error=str(exc))
            raise LLMUnavailableError(f"Ollama error: {exc}")

    async def stream(
        self, messages: list[LLMMessage], system: str = ""
    ) -> AsyncGenerator[str, None]:
        import json
        payload = {
            "model": self._model,
            "messages": [{"role": "system", "content": system}] + [m.to_dict() for m in messages]
            if system
            else [m.to_dict() for m in messages],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST", f"{self._base_url}/api/chat", json=payload
            ) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if content := chunk.get("message", {}).get("content"):
                                yield content
                        except json.JSONDecodeError:
                            continue


# ── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAIClient(BaseLLMClient):
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise LLMUnavailableError(
                "OPENAI_API_KEY is not set. Set it in .env or switch LLM_PROVIDER."
            )
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._timeout = settings.llm_timeout_seconds

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(self, messages: list[LLMMessage], system: str = "") -> str:
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend([m.to_dict() for m in messages])

        try:
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=all_messages,
                    max_tokens=4096,
                ),
                timeout=self._timeout,
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            raise LLMTimeoutError("OpenAI request timed out.")
        except Exception as exc:
            logger.error("openai_error", error=str(exc))
            raise LLMUnavailableError(f"OpenAI error: {exc}")

    async def stream(
        self, messages: list[LLMMessage], system: str = ""
    ) -> AsyncGenerator[str, None]:
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend([m.to_dict() for m in messages])

        async with await self._client.chat.completions.create(
            model=self._model, messages=all_messages, stream=True
        ) as stream:
            async for chunk in stream:
                if delta := chunk.choices[0].delta.content:
                    yield delta


# ── Factory ───────────────────────────────────────────────────────────────────

def get_llm_client(settings: Settings) -> BaseLLMClient:
    """
    Returns the correct LLM client for the configured provider.
    The provider is determined entirely by the LLM_PROVIDER env var.
    """
    provider = settings.llm_provider
    logger.debug("llm_client_selected", provider=provider, model=settings.active_model_name)

    if provider == "anthropic":
        return AnthropicClient(settings)
    if provider == "ollama":
        return OllamaClient(settings)
    if provider == "openai":
        return OpenAIClient(settings)

    raise LLMUnavailableError(
        f"Unknown LLM_PROVIDER '{provider}'. Choose: anthropic | ollama | openai"
    )
