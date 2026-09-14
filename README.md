# 🎙️ Lenny Growth Assistant

An AI-powered conversational web app that answers product and growth questions grounded in **Lenny's Podcast transcripts**. Runs locally with Ollama or in the cloud with Anthropic/OpenAI — switchable via a single env var.

---

## What it does

- **Grounded Q&A** — answers product/growth questions with source citations from transcript chunks
- **Ship 30 for 30 essays** — generates ~1,250-word essays in the Ship 30 style, grounded in transcripts
- **Artifact Viewer** — generates and renders Markdown or sandboxed HTML documents beside the chat
- **Session persistence** — every conversation stored in PostgreSQL with full message history
- **LLM toggle** — switch between Ollama (local), Anthropic Claude, or OpenAI without changing code

---

## Architecture overview

```
Browser (React + Vite)
    │ /api/v1/*
    ▼
FastAPI (Python 3.11)
    ├── Session & message persistence → PostgreSQL
    ├── Agent runner
    │     ├── RAG retrieval → ChromaDB (sentence-transformers embeddings)
    │     ├── LLM client → Ollama | Anthropic | OpenAI
    │     ├── Ship 30 skill
    │     └── Artifact skill
    └── Ingestion pipeline → transcripts/ → ChromaDB
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker + Docker Compose | 24+ | One-command startup |
| Ollama | latest | Local LLM (for demo) |
| Python | 3.11+ | Backend (if running locally) |
| Node.js | 20+ | Frontend (if running locally) |
| PostgreSQL | 15+ | Database (provided by Docker Compose) |

---

## Quick start (Docker Compose — recommended)

```bash
# 1. Clone the repo
git clone <repo-url>
cd lenny-growth-assistant

# 2. Copy and configure env
cp .env.example .env
# Edit .env — set LLM_PROVIDER and add API keys if using cloud

# 3. Start Ollama (runs on host, not in Docker)
ollama serve
ollama pull llama3.2      # or your preferred model

# 4. Start everything
docker-compose up --build

# 5. Index transcripts (one time)
curl -X POST http://localhost:8000/api/v1/ingest

# 6. Open the app
open http://localhost:3000
```

The backend API is at `http://localhost:8000` and the frontend at `http://localhost:3000`.

---

## Local development (without Docker)

### Backend

```bash
cd backend

# Create and activate virtualenv
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and configure
cp ../.env.example ../.env

# Start PostgreSQL (or use a local instance)
# Update DATABASE_URL in .env to point at your local Postgres

# Run the server
python run.py
# or: uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # starts at http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8000` automatically.

---

## Environment variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | ✅ | `ollama` | `ollama` \| `anthropic` \| `openai` |
| `ANTHROPIC_API_KEY` | Cloud only | — | Required when `LLM_PROVIDER=anthropic` |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-20241022` | Anthropic model name |
| `OPENAI_API_KEY` | Cloud only | — | Required when `LLM_PROVIDER=openai` |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | No | `llama3.2` | Ollama model name |
| `DATABASE_URL` | ✅ | postgres connection string | Async PostgreSQL URL |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB storage path |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | sentence-transformers model |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` \| `INFO` \| `WARNING` |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Comma-separated allowed origins |
| `SECRET_KEY` | ✅ prod | random string | App secret — change in production |

---

## Switching LLM providers

No code changes needed — just update `.env` and restart:

```bash
# Use Ollama (local, no API key needed)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2

# Use Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Use OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

The active provider is visible in the UI header badge and in `/api/v1/ready`.

---

## Adding transcripts

Drop `.txt` or `.md` files into `backend/transcripts/`, then re-index:

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/ingest

# Via UI
Click "Index Transcripts" in the sidebar
```

**Filename convention** (optional but recommended):
```
ep042_sean-ellis-growth-hacking.txt
ep107_elena-verna-product-led-growth.txt
```

The ingestion pipeline parses episode numbers and titles from filenames and file headers automatically.

---

## Running tests

```bash
cd backend

# Install test dependencies (already in requirements.txt)
pip install -r requirements.txt

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Run a specific file
pytest tests/test_sessions.py -v
```

Tests use an in-memory SQLite database and a mocked LLM — no Ollama or PostgreSQL needed.

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Liveness probe |
| GET | `/api/v1/ready` | Readiness + model info |
| POST | `/api/v1/sessions` | Create session |
| GET | `/api/v1/sessions` | List sessions |
| GET | `/api/v1/sessions/{id}` | Get session |
| DELETE | `/api/v1/sessions/{id}` | Delete session |
| POST | `/api/v1/chat` | Send message (RAG or skill) |
| GET | `/api/v1/chat/{id}/messages` | Get message history |
| POST | `/api/v1/artifacts` | Generate artifact |
| GET | `/api/v1/artifacts/{id}` | Get artifact |
| GET | `/api/v1/artifacts/session/{id}` | List session artifacts |
| POST | `/api/v1/ingest` | Run transcript ingestion |
| GET | `/api/v1/ingest/status` | Vector store stats |

Full interactive docs at `http://localhost:8000/docs`.

---

## Troubleshooting

**Ollama connection refused**
```
LLMUnavailableError: Cannot connect to Ollama at http://localhost:11434
```
→ Run `ollama serve` and verify the model is pulled: `ollama list`

**Docker: Ollama not reachable from container**
→ The compose file uses `host.docker.internal` — this works on Mac/Windows Docker Desktop. On Linux add `--network=host` or set `OLLAMA_BASE_URL=http://172.17.0.1:11434`.

**Empty retrieval results**
→ Run ingestion: `POST /api/v1/ingest` or click "Index Transcripts" in sidebar. Check `/api/v1/ingest/status` for chunk count.

**Database connection error on startup**
→ Ensure PostgreSQL is running and `DATABASE_URL` is correct. With Docker Compose the DB service must be healthy before the backend starts (handled by `depends_on: condition: service_healthy`).

**Frontend shows blank page**
→ Check browser console. Common cause: CORS mismatch. Ensure `CORS_ORIGINS` includes your frontend URL.

---

## Project structure

```
lenny-growth-assistant/
├── backend/
│   ├── app/
│   │   ├── agent/          # LLM client, agent runner, prompts
│   │   ├── api/routes/     # FastAPI route handlers
│   │   ├── core/           # Config, logging, exceptions
│   │   ├── db/             # SQLAlchemy models, session, CRUD
│   │   ├── ingestion/      # Transcript ingestion pipeline
│   │   ├── retrieval/      # ChromaDB vector store, RAG
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── skills/         # Ship 30, artifact skill prompts
│   │   └── main.py         # FastAPI app entry point
│   ├── transcripts/        # Drop .txt/.md transcript files here
│   ├── tests/              # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # Typed API client
│   │   ├── components/     # React components
│   │   ├── styles/         # Global CSS + Markdown styles
│   │   └── types/          # TypeScript domain types
│   ├── Dockerfile
│   └── nginx.conf
├── docs/                   # PRD, design, architecture, test plan
├── agent-transcripts/      # Coding session logs
├── docker-compose.yml
└── .env.example
```

---

## Demo video

[YouTube link — to be added before submission]

The video covers: problem overview, live demo with Ollama, the artifact viewer, and the LLM provider toggle trade-off.
