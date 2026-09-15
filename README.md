# 🎙️ Lenny Growth Assistant

> An AI-powered product and growth advisor grounded in **Lenny's Podcast transcripts** — ask questions, generate essays, and create documents, all backed by real insights from the world's best product practitioners.

[![Status](https://img.shields.io/badge/Status-Live-brightgreen)](https://github.com/Priyanka-2027/lenny-growth-assistant)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black)](https://ollama.com)

---

## 🎬 Demo Video

> 📹 **[Add your YouTube URL here before submitting]**

*2-minute walkthrough: grounded Q&A, Ship 30 essay, HTML artifact viewer, and local Ollama demo.*

---

## 🤔 What Is This?

[Lenny Rachitsky](https://www.lennysnewsletter.com/) hosts one of the most respected product and growth podcasts in the world. Over 400+ episodes, he has interviewed the best product minds — Brian Chesky (Airbnb), Nikita Bier (tbh, Gas), Ben Horowitz (a16z), Hiten Shah, Jen Abel, and hundreds more.

**The problem:** All that knowledge is buried in hours of audio and thousands of pages of transcripts. Nobody has time to search through it.

**The solution:** The Lenny Growth Assistant turns the entire transcript library into a conversational AI you can ask anything. Every answer is grounded in real transcript excerpts — not hallucinated — and you can see exactly which episode each insight came from.

---

## ✨ Features

### 💬 1. Grounded Q&A (Ask Lenny)
Ask any product or growth question. The system retrieves the most relevant transcript chunks using vector similarity search and gives you a cited answer with expandable sources.

**Example questions:**
- *"How do I find product-market fit?"*
- *"What is the difference between growth loops and funnels?"*
- *"How did Nikita Bier grow tbh and Gas?"*
- *"When should I hire my first salesperson?"*
- *"What does Ben Horowitz say about company culture?"*

### ✍️ 2. Ship 30 for 30 Essay Skill
Generates a ~1,250-word essay in the [Ship 30 for 30](https://www.ship30for30.com/) writing style — structured hook, narrative arc, headings, bullets, and an actionable takeaway. Every claim is grounded in transcript sources.

**Example:** *"Write a Ship 30 essay about the aha moment in onboarding"*

### 📄 3. Markdown Document Generator
Creates well-structured Markdown documents — framework summaries, checklists, PRD templates, meeting notes — rendered live in an artifact viewer beside the chat.

**Example:** *"Create a PMF checklist based on Lenny's transcripts"*

### 🌐 4. HTML Page Generator
Generates complete HTML pages with inline CSS, rendered live in a **sandboxed iframe** beside the chat — just like Claude Artifacts. Scripts are blocked by CSP for security.

**Example:** *"Build an HTML dashboard showing the 5 signals of product-market fit"*

---

## 🏗️ How It Works

```
You type a question
        ↓
Frontend (React) sends it to the FastAPI backend
        ↓
RAG retrieval: finds top-5 relevant transcript chunks in ChromaDB
        ↓
Agent runner: builds prompt with retrieved context + your question
        ↓
LLM (Ollama / Claude / OpenAI) generates grounded answer
        ↓
Response returned with source citations
        ↓
Chat bubble renders with expandable sources
```

### The RAG Pipeline (Retrieval Augmented Generation)

Instead of relying on the LLM's training data (which can hallucinate), we:

1. **Chunk** — Split transcripts into 800-character overlapping chunks
2. **Embed** — Convert each chunk to a 384-dimensional vector using `sentence-transformers`
3. **Store** — Save vectors + metadata in ChromaDB (local vector database)
4. **Retrieve** — On each query, find the top-5 most semantically similar chunks
5. **Ground** — Pass those chunks as context to the LLM: *"Answer only from these excerpts"*

This means every answer is traceable to a real source. No hallucinations.

---

## 🖥️ Screenshots

| Chat with Sources | Ship 30 Essay | Artifact Viewer |
|:-:|:-:|:-:|
| Grounded answers with cited transcript excerpts | ~1,250-word structured essay | Live HTML/Markdown rendering |

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Python web framework, REST API |
| **SQLAlchemy (async)** | Database ORM |
| **SQLite / PostgreSQL** | Stores sessions, messages, artifacts |
| **ChromaDB** | Vector database for transcript embeddings |
| **sentence-transformers** | Local text embeddings (no API key needed) |
| **structlog** | Structured JSON logging |
| **tenacity** | Automatic LLM retry with backoff |
| **Pydantic** | Request/response validation |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tool and dev server |
| **react-markdown** | Markdown rendering in chat |
| **DOMPurify** | HTML sanitization before rendering |

### AI / LLM
| Technology | Purpose |
|-----------|---------|
| **Ollama** | Run LLMs locally on your machine |
| **llama3.2** | Default local model (2GB, no API key) |
| **Anthropic Claude** | Cloud option (better quality) |
| **OpenAI GPT-4o** | Cloud option (alternative) |

---

## 🔄 LLM Provider Toggle

Switch between local and cloud models with **one environment variable** — no code changes:

```bash
# Local (free, private, works offline)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2

# Cloud - Anthropic Claude (best quality)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Cloud - OpenAI GPT-4o
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

The active model is always visible in the UI header badge.

---

## 🗄️ Database Schema

```
sessions         — chat sessions (id, title, metadata, timestamps)
    │
    ├── messages — individual turns (role, content, sources, skill_used, model_used)
    │
    └── artifacts — generated docs (type, title, content)
```

Sessions, messages, and artifacts are all persisted. Deleting a session removes everything under it.

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Liveness check |
| GET | `/api/v1/ready` | Readiness + active model info |
| POST | `/api/v1/sessions` | Create a new chat session |
| GET | `/api/v1/sessions` | List all sessions |
| GET | `/api/v1/sessions/{id}` | Get a session |
| DELETE | `/api/v1/sessions/{id}` | Delete session + all messages |
| POST | `/api/v1/chat` | Send a message, get AI response |
| GET | `/api/v1/chat/{id}/messages` | Get message history |
| POST | `/api/v1/artifacts` | Generate a Markdown or HTML artifact |
| GET | `/api/v1/artifacts/{id}` | Get an artifact |
| POST | `/api/v1/ingest` | Index transcripts into ChromaDB |
| GET | `/api/v1/ingest/status` | Vector store stats |

Interactive API docs: **http://localhost:8000/docs**

---

## 🚀 Quick Start

> 📖 **For the complete step-by-step guide, see [SETUP.md](SETUP.md)**

### TL;DR (for experienced developers)

```bash
# 1. Clone
git clone https://github.com/Priyanka-2027/lenny-growth-assistant.git
cd lenny-growth-assistant

# 2. Configure (SQLite + Ollama by default — no database setup needed)
cp .env.example .env

# 3. Pull the LLM model (~2GB)
ollama serve          # terminal 1 — keep running
ollama pull llama3.2  # terminal 2

# 4. Backend (use Python 3.11 specifically)
cd backend
py -3.11 -m venv .venv        # Windows
# python3.11 -m venv .venv    # Mac/Linux
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
cp ../.env .env
python run.py                  # terminal 2

# 5. Index transcripts (run once)
# Windows:
Invoke-WebRequest -Uri http://localhost:8000/api/v1/ingest -Method POST
# Mac/Linux:
# curl -X POST http://localhost:8000/api/v1/ingest

# 6. Frontend
cd ../frontend
npm install
npm run dev                    # terminal 3

# 7. Open http://localhost:5173
```

**Having issues?** See the [Troubleshooting section in SETUP.md](SETUP.md#troubleshooting)

---

## 🐳 Docker Compose (One Command)

If you have Docker installed:

```bash
cp .env.example .env
# Edit .env with your settings

docker-compose up --build
```

Then open **http://localhost:3000**

> **Note:** Ollama runs on your host machine, not inside Docker. Make sure `ollama serve` is running before starting Docker Compose.

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | ✅ | `ollama` | `ollama` / `anthropic` / `openai` |
| `ANTHROPIC_API_KEY` | Cloud only | — | Your Anthropic API key |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-20241022` | Claude model name |
| `OPENAI_API_KEY` | Cloud only | — | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o` | OpenAI model name |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | No | `llama3.2` | Ollama model name |
| `DATABASE_URL` | ✅ | SQLite connection | Database connection string |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB storage path |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | sentence-transformers model |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` / `INFO` / `WARNING` |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Allowed frontend origins |
| `SECRET_KEY` | ✅ prod | random | Change in production |

---

## 📚 Adding More Transcripts

Drop any `.txt` or `.md` files into `backend/transcripts/`, then re-index:

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/ingest

# Via UI
Click "Index Transcripts" in the sidebar
```

**Recommended filename format:**
```
ep042_sean-ellis-growth-hacking.txt
ep107_elena-verna-product-led-growth.txt
```

The ingestion pipeline automatically parses episode numbers and guest names from filenames.

**Currently indexed (6 transcripts):**
- Episode 001 — How to Find Product-Market Fit (Lenny Rachitsky)
- Episode 002 — Growth Loops vs Funnels (Brian Balfour)
- Episode 003 — Onboarding and Activation (Hiten Shah)
- Nikita Bier — How to Build Viral Consumer Apps
- Jen Abel — The Ultimate Guide to Founder-Led Sales
- Ben Horowitz — Hard Truths: Why Founders Fail

---

## 🔒 Security

### HTML Artifact Isolation
Generated HTML is rendered inside a sandboxed `<iframe>`:

```html
<iframe sandbox="allow-same-origin" srcDoc={html} />
```

Combined with a CSP meta tag injected into every generated HTML:
```html
<meta http-equiv="Content-Security-Policy" content="script-src 'none'; object-src 'none';">
```

**What this blocks:** JavaScript execution, form submission, popups, external requests, cookies  
**What this permits:** CSS styling, static text, images from data URIs

### No Secrets in Code
All API keys and credentials are read from environment variables. The `.env` file is in `.gitignore` and never committed.

---

## 🧪 Running Tests

```bash
cd backend

# Activate virtual environment first
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_sessions.py -v
```

**Tests use:**
- In-memory SQLite (no real database needed)
- Mocked LLM (no Ollama or API keys needed)
- 7 test files, 40+ test functions

**Test coverage:**
- `test_health.py` — liveness and readiness endpoints
- `test_sessions.py` — full session CRUD
- `test_chat.py` — message sending, persistence, skill routing
- `test_artifacts.py` — artifact generation and retrieval
- `test_crud.py` — all database operations
- `test_retrieval.py` — vector store, ingestion pipeline, RAG
- `test_skills.py` — Ship 30 and artifact prompt engineering

---

## 🔧 Troubleshooting

**Ollama connection refused**
```
LLMUnavailableError: Cannot connect to Ollama at http://localhost:11434
```
→ Run `ollama serve` in a terminal and keep it running

**Model not found (404)**
```
Client error '404 Not Found' for url http://localhost:11434/api/chat
```
→ Pull the model first: `ollama pull llama3.2`

**Database connection error**
```
db_init_failed: getaddrinfo failed
```
→ Your PostgreSQL/Supabase URL is wrong or the server is down. Switch to SQLite:
```bash
DATABASE_URL=sqlite+aiosqlite:///./lenny_demo.db
```

**Empty retrieval results**
```
Knowledge base: 0 chunks
```
→ Run ingestion: `POST /api/v1/ingest` or click "Index Transcripts" in sidebar

**Frontend blank page**
→ Check browser console. Usually CORS — make sure `CORS_ORIGINS` includes your frontend URL

**Python 3.14 build failures**
→ Use Python 3.11: `py -3.11 -m venv .venv`

---

## 📁 Project Structure

```
lenny-growth-assistant/
│
├── .env.example              ← Copy to .env and configure
├── docker-compose.yml        ← One-command Docker startup
├── README.md
│
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── llm_client.py     ← Ollama/Anthropic/OpenAI abstraction
│   │   │   ├── prompts.py        ← System prompt templates
│   │   │   └── runner.py         ← Agent orchestration + skill routing
│   │   ├── api/routes/
│   │   │   ├── health.py         ← /health and /ready endpoints
│   │   │   ├── sessions.py       ← Session CRUD
│   │   │   ├── chat.py           ← Chat endpoint (main flow)
│   │   │   ├── artifacts.py      ← Artifact generation
│   │   │   └── ingest.py         ← Transcript indexing
│   │   ├── core/
│   │   │   ├── config.py         ← All config via env vars
│   │   │   ├── logging.py        ← Structured JSON logging
│   │   │   └── exceptions.py     ← Typed error hierarchy
│   │   ├── db/
│   │   │   ├── models.py         ← SQLAlchemy ORM models
│   │   │   ├── session.py        ← DB engine + get_db() dependency
│   │   │   └── crud.py           ← All DB operations
│   │   ├── ingestion/
│   │   │   └── pipeline.py       ← Transcript → chunks → ChromaDB
│   │   ├── retrieval/
│   │   │   ├── vector_store.py   ← ChromaDB wrapper
│   │   │   └── rag.py            ← Query → context block
│   │   └── skills/
│   │       ├── ship30.py         ← Ship 30 writing principles
│   │       └── artifact_skill.py ← Markdown/HTML system prompts
│   ├── transcripts/              ← Add .txt/.md files here
│   ├── tests/                    ← pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx    ← Main chat interface
│   │   │   │   ├── MessageBubble.tsx ← Individual message rendering
│   │   │   │   ├── SkillSelector.tsx ← Skill toggle buttons
│   │   │   │   └── SourceList.tsx    ← Collapsible source citations
│   │   │   ├── artifact/
│   │   │   │   └── ArtifactViewer.tsx ← Sandboxed iframe viewer
│   │   │   └── sidebar/
│   │   │       └── Sidebar.tsx       ← Session list + ingest button
│   │   ├── api/
│   │   │   └── client.ts             ← Typed API client
│   │   ├── styles/
│   │   │   ├── globals.css           ← Dark theme CSS variables
│   │   │   └── markdown.css          ← Markdown rendering styles
│   │   └── types/
│   │       └── index.ts              ← TypeScript domain types
│   ├── Dockerfile
│   └── nginx.conf
│
├── docs/
│   ├── PRD.md                ← Product requirements document
│   ├── architecture.md       ← Technical architecture
│   ├── design.md             ← UI/UX design decisions
│   └── manual_test_plan.md   ← Manual QA checklist
│
└── agent-transcripts/
    ├── README.md
    └── session-01-build-log.md  ← Full build log with failures and fixes
```

---

## 🗺️ Roadmap (Future Improvements)

- [ ] Streaming responses (SSE) for real-time token display
- [ ] Authentication and multi-user support
- [ ] Cross-encoder reranker for better retrieval quality
- [ ] Automatic transcript ingestion from RSS feed
- [ ] Mobile-responsive layout
- [ ] Conversation export (PDF, Markdown)
- [ ] More transcript sources beyond Lenny's Podcast

---

## 📄 Documentation

| Document | Contents |
|----------|---------|
| [PRD.md](docs/PRD.md) | Discovery brief, user problem, success metrics, assumptions, risks |
| [architecture.md](docs/architecture.md) | DB schema, API endpoints, ingestion flow, security model |
| [design.md](docs/design.md) | UI/UX principles, color system, interaction states, accessibility |
| [manual_test_plan.md](docs/manual_test_plan.md) | Step-by-step UI test checklist |
| [agent-transcripts/](agent-transcripts/) | Full build log including failures and how they were fixed |

---

## 🙏 Acknowledgements

- **[Lenny Rachitsky](https://www.lennysnewsletter.com/)** — for making podcast transcripts publicly available
- **[ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts)** — public transcript archive used as knowledge base
- **[Ollama](https://ollama.com)** — for making local LLMs accessible
- **[ChromaDB](https://www.trychroma.com/)** — lightweight vector database
- **[sentence-transformers](https://www.sbert.net/)** — local embedding model

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🗃️ Database Note

The demo runs on **SQLite** by default for zero-setup local running. To switch to PostgreSQL (Supabase, Railway, or local Postgres), update `DATABASE_URL` in `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres?ssl=require
```

The codebase supports both — SQLAlchemy handles the dialect automatically.

---

*Built as a Forward Deployed Engineer take-home assessment — September 2026*
