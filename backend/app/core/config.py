"""
Application configuration — driven entirely by environment variables.
Switch LLM provider by setting LLM_PROVIDER=anthropic|ollama|openai.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_env: Literal["development", "production", "test"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    secret_key: str = "change-me-insecure-default"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── LLM Provider ─────────────────────────────────────────────────────────
    llm_provider: Literal["anthropic", "ollama", "openai"] = "ollama"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    @property
    def active_model_name(self) -> str:
        """Human-readable model identifier for UI / logs."""
        if self.llm_provider == "anthropic":
            return f"anthropic/{self.anthropic_model}"
        if self.llm_provider == "openai":
            return f"openai/{self.openai_model}"
        return f"ollama/{self.ollama_model}"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_db"
    )

    # ── Vector Store ─────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "lenny_transcripts"

    # ── Embeddings ───────────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── RAG ──────────────────────────────────────────────────────────────────
    retrieval_top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 100

    # ── Timeouts ─────────────────────────────────────────────────────────────
    llm_timeout_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — use as FastAPI dependency."""
    return Settings()
