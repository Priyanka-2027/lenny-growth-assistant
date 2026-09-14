# Architecture Document
## The Lenny Growth Assistant

**Version:** 1.0  
**Date:** September 2026

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│           React 18 + TypeScript + Vite (port 5173/3000)     │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP /api/v1/*
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI (port 8000)                         │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   Routes     │  │   Agent     │  │   Ingestion      │   │
│  │ /sessions    │  │   Runner    │  │   Pipeline       │   │
│  │ /chat        │  │             │  │                  │   │
│  │ /artifacts   │  │  ┌────────┐ │  │  transcripts/    │   │
│  │ /ingest      │  │  │  RAG   │ │  │  → chunk         │   │
│  │ /health      │  │  └────────┘ │  │  → embed         │   │
│  └──────┬───────┘  │  ┌────────┐ │  │  → upsert        │   │
│         │          │  │Skills  │ │  └────────┬─────────┘   │
│         │          │  └────────┘ │           │             │
│         │          │  ┌────────┐ │           │             │
│         │          │  │  LLM   │ │           │             │
│         │          │  │Client  │ │           │             │
│         │          │  └───┬────┘ │           │             │
│         │          └──────┼──────┘           │             │
└─────────┼─────────────────┼──────────────────┼─────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
   ┌──────────┐    ┌─────────────────┐  ┌──────────────┐
   │PostgreSQL│    │ Ollama /        │  │  ChromaDB    │
   │(sessions,│    │ Anthropic /     │  │(vector store)│
   │messages, │    │ OpenAI          │  │              │
   │artifacts)│    └─────────────────┘  └──────────────┘
   └──────────┘
```

---

## 2. Database Schema

### `sessions`
```sql
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(200),
    user_metadata JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `messages`
```sql
CREATE TABLE messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL,          -- user | assistant | system
    content     TEXT NOT NULL,
    sources     JSONB,                          -- list of Source objects
    skill_used  VARCHAR(50),                    -- ship30 | artifact_md | artifact_html
    model_used  VARCHAR(100),                   -- provider/model string
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_messages_session_id ON messages(session_id);
```

### `artifacts`
```sql
CREATE TABLE artifacts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id     UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    artifact_type  VARCHAR(20) NOT NULL,        -- markdown | html
    title          VARCHAR(200) NOT NULL,
    content        TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_artifacts_session_id ON artifacts(session_id);
```

**Design choices:**
- UUID PKs: no sequential ID leakage, safe to expose in URLs
- JSONB for `sources` and `user_metadata`: flexible schema for evolving citation structure
- Cascade delete: removing a session removes all messages and artifacts (clean isolation)
- `updated_at` on sessions: touched on every new message for "recent first" ordering

---

## 3. API Endpoints

### Health
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | None | Liveness probe — always 200 if process is up |
| GET | `/api/v1/ready` | None | Readiness — checks DB + returns active model |

### Sessions
| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/api/v1/sessions` | `{title?, user_metadata?}` | `SessionResponse` (201) |
| GET | `/api/v1/sessions` | `?limit&offset` | `SessionListResponse` |
| GET | `/api/v1/sessions/{id}` | — | `SessionResponse` |
| DELETE | `/api/v1/sessions/{id}` | — | 204 |

### Chat
| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/api/v1/chat` | `{session_id, message, skill?}` | `ChatResponse` |
| GET | `/api/v1/chat/{session_id}/messages` | — | `Message[]` |

`skill` values: `null` (RAG), `"ship30"`, `"artifact_md"`, `"artifact_html"`

### Artifacts
| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/api/v1/artifacts` | `{session_id, artifact_type, title, instructions}` | `ArtifactResponse` (201) |
| GET | `/api/v1/artifacts/{id}` | — | `ArtifactResponse` |
| GET | `/api/v1/artifacts/session/{id}` | — | `ArtifactResponse[]` |

### Ingestion
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ingest` | Run ingestion pipeline on `transcripts/` |
| GET | `/api/v1/ingest/status` | Vector store chunk count |

### Error responses
All errors follow: `{"error": "human-readable message"}`  
HTTP status codes: 400 (bad request), 404 (not found), 422 (validation), 503 (LLM unavailable), 504 (timeout)

---

## 4. Component Boundaries

### `app/core/`
Pure configuration and cross-cutting concerns — no business logic.
- `config.py` — pydantic-settings, `get_settings()` singleton
- `logging.py` — structlog setup, `get_logger()`
- `exceptions.py` — typed exception hierarchy, HTTP mapping

### `app/db/`
Data layer only. No business logic, no LLM calls.
- `base.py` — SQLAlchemy declarative base, shared mixins
- `models.py` — ORM models
- `session.py` — async engine, `get_db()` dependency, `init_db()`
- `crud.py` — all DB operations, returns ORM objects

### `app/schemas/`
Pydantic models for API contracts. No DB dependencies.

### `app/agent/`
Orchestration layer. Coordinates retrieval + skills + LLM.
- `llm_client.py` — provider abstraction (`BaseLLMClient`, `get_llm_client()` factory)
- `prompts.py` — system prompt templates
- `runner.py` — `AgentRunner` — skill routing + RAG + LLM calls

### `app/retrieval/`
Vector store access only.
- `vector_store.py` — ChromaDB wrapper, embed + add + query
- `rag.py` — retrieve context + format for LLM injection

### `app/ingestion/`
One-direction data pipeline. Reads files, writes to vector store.
- `pipeline.py` — scan → parse → chunk → embed → upsert

### `app/skills/`
Prompt engineering only. Pure functions, no I/O.
- `ship30.py` — Ship 30 system prompt + prompt builder
- `artifact_skill.py` — Markdown/HTML system prompts + prompt builders

### `app/api/routes/`
HTTP boundary only. Validates input, calls business logic, returns schemas.

---

## 5. Ingestion and Retrieval Flow

### Ingestion
```
transcripts/*.txt|*.md
  ↓ read_text()
  ↓ _parse_metadata(filename, content)    # episode, title, guest
  ↓ RecursiveCharacterTextSplitter        # chunk_size=800, overlap=100
  ↓ _make_chunk_id(filename, index)       # SHA256 → 24-char stable ID
  ↓ SentenceTransformer.encode()          # all-MiniLM-L6-v2, normalized
  ↓ chromadb.collection.upsert()          # idempotent by chunk_id
```

**Chunking strategy:**
- `RecursiveCharacterTextSplitter` splits on `\n\n` → `\n` → `. ` → space → char
- 800-char chunks preserve enough context for a single speaker turn
- 100-char overlap prevents ideas that span chunk boundaries from being lost
- Chunk IDs are SHA256(filename + index) — deterministic, survives re-indexing

**Embedding model choice:** `all-MiniLM-L6-v2` (sentence-transformers)
- 384-dimensional embeddings, 22M parameters
- Fast on CPU (~50ms per chunk), no API key needed
- Strong semantic similarity for English text
- Trade-off: lower ceiling than OpenAI `text-embedding-3-large` — acceptable for a local demo

### Retrieval
```
user_query
  ↓ SentenceTransformer.encode()
  ↓ chromadb.collection.query(top_k=5, cosine similarity)
  ↓ filter chunks by score (implicit — top_k returns best matches)
  ↓ format as RELEVANT TRANSCRIPT EXCERPTS block
  ↓ inject into LLM system prompt
  ↓ LLM generates answer with inline citations
  ↓ return (context_block, sources[])
```

**Why top-5?** Balances context richness against prompt token cost. For long transcripts, top-5 × 800 chars = ~4,000 chars of context — well within LLM context windows but not wasteful.

---

## 6. Agent Routing

```
POST /api/v1/chat
  ↓ AgentRunner.run(message, history, skill)
  ├── skill=None       → _run_rag()       # grounded Q&A
  ├── skill="ship30"   → _run_ship30()    # ~1,250-word essay
  ├── skill="artifact_md"  → _run_artifact_inline("markdown")
  └── skill="artifact_html" → _run_artifact_inline("html")
```

All routes retrieve context first (RAG), then apply the skill-specific system prompt. History is injected as prior conversation turns for multi-turn coherence.

---

## 7. LLM Provider Toggle

```python
# app/agent/llm_client.py
def get_llm_client(settings: Settings) -> BaseLLMClient:
    if settings.llm_provider == "anthropic": return AnthropicClient(settings)
    if settings.llm_provider == "ollama":    return OllamaClient(settings)
    if settings.llm_provider == "openai":    return OpenAIClient(settings)
```

Each client implements `BaseLLMClient`:
- `complete(messages, system) → str` — for all skills
- `stream(messages, system) → AsyncGenerator[str, None]` — available but not used in v1

**Fallback behavior:**
- Missing API key → `LLMUnavailableError` raised at client instantiation (startup time, not request time)
- Ollama not running → `LLMUnavailableError` with clear "run `ollama serve`" message
- Request timeout → `LLMTimeoutError` after `LLM_TIMEOUT_SECONDS` (default 120s)
- Retries: Anthropic/OpenAI retry 3× with exponential backoff; Ollama retries 2×

---

## 8. Security

### HTML Artifact Isolation
Generated HTML is untrusted content. Defense-in-depth approach:

```
iframe sandbox="allow-same-origin"
  ↓ Blocks: script execution, form submission, popups, plugins
  ↓ Permits: CSS rendering, static text, data URIs
  
+ CSP meta tag injected into HTML head:
  <meta http-equiv="Content-Security-Policy"
        content="script-src 'none'; object-src 'none';">

+ Nginx header on all responses:
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'...
```

`allow-same-origin` without `allow-scripts` means the iframe can access its own origin for CSS but cannot execute JavaScript. This is the most restrictive sandbox that still permits CSS styling.

**What this blocks:** XSS, `<script>` tags, `eval()`, `fetch()`, cookie access, localStorage access, form submission.  
**What this permits:** CSS (`<style>` tags and inline), static text, images from data URIs.

### Markdown Sanitization
Markdown content rendered via `react-markdown` + DOMPurify:
- `DOMPurify.sanitize()` strips any raw HTML that could carry `<script>` tags
- `remark-gfm` parses tables, checkboxes, strikethrough — no eval
- `dangerouslySetInnerHTML` is not used anywhere in the codebase

### API Security
- Input validation via Pydantic — all request fields typed and bounded
- UUID validation for path parameters — invalid UUIDs return 422, not 500
- CORS restricted to configured origins via `CORS_ORIGINS` env var
- No secrets in responses; DB IDs are UUIDs (not sequential, not guessable)

---

## 9. Observability

All logs are structured JSON in production, pretty-printed in development.

**Key log events:**
| Event | Level | Fields |
|-------|-------|--------|
| `starting_up` | INFO | env, provider, model |
| `database_ready` | INFO | — |
| `session_created` | INFO | session_id |
| `chat_response_generated` | INFO | session_id, skill, sources_count, model |
| `context_retrieved` | INFO | query_preview, chunks, top_score |
| `transcript_ingested` | INFO | file, chunks |
| `llm_error` | ERROR | error |
| `retrieval_failed` | ERROR | error |
| `app_error` | ERROR | detail, path |
| `unhandled_exception` | ERROR | path, exc |
| `request_handled` | DEBUG | method, path, status, ms |

Response time is tracked via `X-Process-Time-Ms` response header.

---

## 10. Deployment Topology

### Local development
```
localhost:5173  →  Vite dev server (React, HMR)
                        ↓ proxy /api → localhost:8000
localhost:8000  →  uvicorn (FastAPI, --reload)
localhost:5432  →  PostgreSQL (local install)
localhost:11434 →  Ollama (local install)
./chroma_db/    →  ChromaDB persistent files
```

### Docker Compose
```
host:3000   →  [frontend] nginx:alpine
                    ↓ proxy /api → backend:8000
host:8000   →  [backend] python:3.11-slim (uvicorn)
                    ↓ postgresql+asyncpg://db:5432
                    ↓ http://host.docker.internal:11434 (Ollama on host)
                    ↓ /app/chroma_db (volume: chroma_data)
host:5432   →  [db] postgres:16-alpine
                    ↓ volume: postgres_data

Volumes:
  postgres_data  → persistent across restarts
  chroma_data    → persistent across restarts
```

### Future production hardening (not in scope for v1)
- Replace single uvicorn worker with `--workers 4` or gunicorn
- Add Redis for session caching and rate limiting
- Add authentication (OAuth2 / API keys)
- Move ChromaDB to a managed vector store (Pinecone, Weaviate)
- Add a cross-encoder reranker for retrieval quality
- Enable streaming responses via SSE
