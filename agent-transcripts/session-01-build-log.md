# Agent Session Log — Full Build

**Date:** September 15, 2026  
**Agent:** Kiro (Claude-based)  
**Total duration:** ~6 hours  

---

## Session Overview

Built the complete Lenny Growth Assistant from scratch using an AI coding agent. This log documents the key decisions, failures, and corrections made during the build.

---

## Phase 1 — Project Scaffold

**What was done:**
- Created full directory structure: `backend/app/{api,agent,core,db,ingestion,retrieval,skills,schemas}`, `frontend/`, `docs/`, `agent-transcripts/`
- Wrote `.gitignore`, `.env.example`, `requirements.txt`
- Built `core/config.py` using pydantic-settings — all config driven by env vars

**Key decision:** Used `LLM_PROVIDER` as a single env var to toggle between ollama/anthropic/openai. No `if/else` in business logic — just a factory function in `llm_client.py`.

---

## Phase 2 — Backend: DB Models + CRUD

**What was done:**
- SQLAlchemy async models: `Session`, `Message`, `Artifact`
- UUID primary keys (not sequential — safe to expose in URLs)
- JSONB for `sources` and `user_metadata` — flexible schema
- Cascade delete: remove session → removes all messages and artifacts

**Failure #1:** Initial `session.py` used `pool_size` and `max_overflow` parameters.  
**Error:** `TypeError: Invalid argument(s) 'pool_size','max_overflow' for SQLiteDialect`  
**Fix:** Added `_get_engine_kwargs()` helper that returns different params based on dialect — SQLite uses `StaticPool`, PostgreSQL uses connection pool settings.

---

## Phase 3 — LLM Client Abstraction

**What was done:**
- `BaseLLMClient` with `complete()` and `stream()` interface
- `AnthropicClient`, `OllamaClient`, `OpenAIClient` all implement same interface
- `get_llm_client(settings)` factory — returns correct client based on `LLM_PROVIDER`
- Tenacity retry decorator: Anthropic/OpenAI retry 3x, Ollama retries 2x

**Key decision:** Used `tenacity` for retries rather than manual retry loops. Exponential backoff with `wait_exponential(min=1, max=10)`.

---

## Phase 4 — RAG Pipeline

**What was done:**
- `ingestion/pipeline.py`: scans `transcripts/`, chunks with `RecursiveCharacterTextSplitter` (800 chars, 100 overlap), embeds with sentence-transformers, upserts to ChromaDB
- Chunk IDs = SHA256(filename + index) — deterministic, idempotent re-ingestion
- `retrieval/vector_store.py`: ChromaDB wrapper with cosine similarity
- `retrieval/rag.py`: query → top-5 chunks → formatted context block

**Failure #2:** `get_vector_store()` used `@lru_cache` decorator.  
**Error:** `TypeError: unhashable type: 'Settings'` — Pydantic Settings objects aren't hashable.  
**Fix:** Replaced `@lru_cache` with a module-level `_vector_store_instance` global singleton pattern.

---

## Phase 5 — Agent Runner + Skills

**What was done:**
- `AgentRunner.run()` routes by skill: `None` → RAG, `ship30` → Ship30 skill, `artifact_md/html` → artifact inline
- `skills/ship30.py`: encoded 7 Ship 30 writing principles as system prompt rules (not free-form)
- `skills/artifact_skill.py`: separate system prompts for Markdown vs HTML, HTML explicitly says "NO JavaScript"

**Key decision:** Skills are pure functions that return (system_prompt, user_message) tuples. No I/O, fully testable in isolation.

---

## Phase 6 — FastAPI Routes

**What was done:**
- 5 route modules: health, sessions, chat, artifacts, ingest
- All use Pydantic schemas for validation
- Global exception handler catches `AppError` subclasses → structured JSON responses
- Request timing middleware adds `X-Process-Time-Ms` header

---

## Phase 7 — React Frontend

**Failure #3:** `npm create vite` on Windows PowerShell requires interactive prompt (y/n confirmation).  
**Fix:** Scaffolded all frontend files manually — `package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`, all source files.

**What was built:**
- `App.tsx`: session management, health check on mount, model info display
- `Sidebar.tsx`: session list, new chat button, ingest trigger, chunk count
- `ChatWindow.tsx`: message history, skill selector, auto-resize textarea, optimistic UI
- `MessageBubble.tsx`: react-markdown rendering for assistant messages
- `SourceList.tsx`: collapsible source citations
- `ArtifactViewer.tsx`: sandboxed iframe for HTML, react-markdown for MD, copy/download buttons
- `ModelBadge.tsx`: shows active provider/model in header

**TypeScript errors fixed:**
- `ArtifactPayload` imported but unused in `client.ts` → removed
- `React` imported but unused in `App.tsx` → removed (React 18 JSX transform)
- `onOpenArtifact` prop destructured but unused in `MessageBubble` → removed from destructuring

**Build result:** `✓ 295 modules transformed` — zero TypeScript errors.

---

## Phase 8 — Docker + Deployment

**What was done:**
- `docker-compose.yml`: postgres + backend + frontend services with health checks
- `backend/Dockerfile`: multi-stage python:3.11-slim
- `frontend/Dockerfile`: node:20-alpine build → nginx:alpine serve
- `frontend/nginx.conf`: proxy `/api` to backend, SPA fallback, security headers, gzip

---

## Phase 9 — Tests

**What was done:**
- `conftest.py`: in-memory SQLite + mocked `AgentRunner` — no real LLM or DB needed
- 7 test files, 40+ test functions covering: health, sessions, chat, artifacts, CRUD, retrieval, skills
- `pytest.ini`: asyncio_mode=auto

---

## Phase 10 — Local Startup Issues

**Failure #4:** Python 3.14 (default) couldn't build `pydantic-core`, `asyncpg`, `chromadb` — no pre-built wheels.  
**Fix:** Used `py -3.11` to create venv with Python 3.11.

**Failure #5:** `tiktoken` requires Rust compiler to build from source.  
**Fix:** Removed `tiktoken` from `requirements.txt` — it was only used for token counting which isn't critical for the demo.

**Failure #6:** Supabase project hostname `db.ouboxskzcdggbavomaxl.supabase.co` returned DNS NXDOMAIN.  
**Root cause:** Supabase free tier project was in "Unhealthy" state.  
**Fix:** Switched to SQLite (`sqlite+aiosqlite:///./lenny_demo.db`) for the demo. PostgreSQL support remains in the codebase — just update `DATABASE_URL`.

**Failure #7:** uvicorn reloader kept restarting because it watched `.venv/` directory (thousands of files changing during pip install).  
**Fix:** Set `reload=False` in `run.py`.

**Failure #8:** `ollama pull llama3.2` not recognized — Ollama installed but not in PATH.  
**Fix:** Used full path `C:\Users\DELL\AppData\Local\Programs\Ollama\ollama.exe pull llama3.2` or opened fresh terminal.

---

## Final State

- Backend: FastAPI on port 8000, SQLite DB, ChromaDB with 47 chunks
- Frontend: React on port 5173
- LLM: Ollama llama3.2 (2GB, local)
- All 4 skills working: RAG Q&A, Ship 30 essay, Markdown artifact, HTML artifact
- Sources shown per response
- Model badge visible in UI
