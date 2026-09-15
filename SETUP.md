# 🚀 Setup Guide — Lenny Growth Assistant

This guide takes you from a fresh clone to a fully running app.  
Estimated time: **10–15 minutes** (mostly downloading the LLM model).

---

## Prerequisites

Before you start, install these:

| Tool | Version | Download |
|------|---------|----------|
| Python | **3.11** (not 3.12+) | [python.org/downloads](https://www.python.org/downloads/release/python-3119/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Ollama | latest | [ollama.com/download](https://ollama.com/download) |
| Git | any | [git-scm.com](https://git-scm.com) |

> ⚠️ **Python version matters.** Use Python 3.11 specifically. Python 3.12+ breaks several ML packages (`chromadb`, `sentence-transformers`). On Windows use `py -3.11`, on Mac/Linux use `python3.11`.

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/Priyanka-2027/lenny-growth-assistant.git
cd lenny-growth-assistant
```

---

## Step 2 — Configure environment

```bash
cp .env.example .env
```

**The default `.env` works out of the box** — it uses:
- Ollama (local LLM, free, no API key)
- SQLite (local database, zero setup)

You only need to edit `.env` if you want to use Anthropic Claude or OpenAI instead:

```bash
# To use Anthropic Claude (optional):
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

# To use OpenAI (optional):
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

---

## Step 3 — Install and start Ollama

**Download Ollama** from [ollama.com/download](https://ollama.com/download) and install it.

Then open a terminal and run:

```bash
# Start the Ollama server (keep this terminal open)
ollama serve
```

Open a **second terminal** and pull the model (~2GB download, takes 2-5 min):

```bash
ollama pull llama3.2
```

Wait for `success` before continuing.

> **Verify it worked:**
> ```bash
> ollama list
> ```
> You should see `llama3.2` in the list.

---

## Step 4 — Set up the backend

Open a **new terminal** in the project root:

### Windows (PowerShell)

```powershell
cd backend

# Create virtual environment with Python 3.11
py -3.11 -m venv .venv

# Activate it
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Mac / Linux

```bash
cd backend

# Create virtual environment with Python 3.11
python3.11 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> ⏳ This takes 3–5 minutes (downloading PyTorch, sentence-transformers, etc.)

---

## Step 5 — Copy .env to backend folder

The backend reads `.env` from its own directory:

### Windows

```powershell
Copy-Item ..\.env .env
```

### Mac / Linux

```bash
cp ../.env .env
```

---

## Step 6 — Start the backend

Still inside the `backend/` folder with the venv activated:

```bash
python run.py
```

You should see:

```
INFO: Started server process
INFO: Waiting for application startup.
[info] starting_up   provider=ollama  model=ollama/llama3.2
[info] database_ready
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

✅ **Backend is running.** Leave this terminal open.

> **Verify:** Open http://localhost:8000/api/v1/health — should return `{"status":"ok"}`

---

## Step 7 — Index transcripts

Open a **new terminal**, navigate to `backend/`, activate the venv, then:

### Windows

```powershell
cd backend
.venv\Scripts\activate
Invoke-WebRequest -Uri http://localhost:8000/api/v1/ingest -Method POST | Select-Object -ExpandProperty Content
```

### Mac / Linux

```bash
cd backend
source .venv/bin/activate
curl -X POST http://localhost:8000/api/v1/ingest
```

You should see:

```json
{"status":"ok","transcripts_processed":6,"chunks_indexed":47,"message":"Successfully indexed 47 chunks from 6 transcripts."}
```

✅ **Knowledge base is ready.**

---

## Step 8 — Start the frontend

Open a **new terminal** in the project root:

```bash
cd frontend
npm install
npm run dev
```

You should see:

```
  VITE v5.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

✅ **Frontend is running.**

---

## Step 9 — Open the app

Go to **http://localhost:5173** in your browser.

You should see the Lenny Growth Assistant with:
- A dark chat interface
- `ollama/llama3.2` badge in the top right
- "Knowledge base: 47 chunks" in the bottom left sidebar
- A "New Chat" button

---

## Step 10 — Try it out

1. Click **"New Chat"**
2. Make sure **"Ask Lenny"** skill is selected (default)
3. Ask: `How do I find product-market fit?`
4. Wait 10–30 seconds (local LLM is slower than cloud)
5. See a grounded answer with source citations

---

## Summary — What should be running

| Terminal | Command | URL |
|----------|---------|-----|
| 1 | `ollama serve` | http://localhost:11434 |
| 2 | `python run.py` (in backend/) | http://localhost:8000 |
| 3 | `npm run dev` (in frontend/) | http://localhost:5173 |

---

## Troubleshooting

### ❌ `ollama: command not found`
Ollama isn't in your PATH. Try the full path:
- **Windows:** `C:\Users\YOUR_NAME\AppData\Local\Programs\Ollama\ollama.exe serve`
- **Mac:** `/usr/local/bin/ollama serve`

Or close your terminal and open a new one after installing Ollama.

---

### ❌ `ModuleNotFoundError: No module named 'pydantic'`
The venv isn't activated. Run:
- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

You should see `(.venv)` at the start of your terminal prompt.

---

### ❌ Python build errors during `pip install`
You're using Python 3.12 or 3.14. Use Python 3.11:

```bash
# Check your Python version
python --version

# Windows — use py launcher to target 3.11
py -3.11 -m venv .venv

# Mac — install Python 3.11 via pyenv or homebrew
brew install python@3.11
python3.11 -m venv .venv
```

---

### ❌ Backend exits immediately after `Application startup complete`
The file watcher is restarting it. This is fixed by default — `run.py` uses `reload=False`. If it still happens, run directly:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

### ❌ `404 Not Found` when sending a chat message
The LLM model isn't pulled yet. Run:

```bash
ollama pull llama3.2
```

Wait for `success`, then try again.

---

### ❌ `Unable to connect to remote server` when indexing
The backend isn't running. Make sure Terminal 2 shows `Uvicorn running on http://0.0.0.0:8000` before running the ingest command.

---

### ❌ Knowledge base shows 0 chunks
Ingestion hasn't run yet. Go back to Step 7 and run the ingest command.

---

### ❌ Frontend shows blank page
Check the browser console (F12 → Console). Usually a CORS issue. Make sure `CORS_ORIGINS` in your `.env` includes `http://localhost:5173`.

---

## Running Tests

```bash
cd backend
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Mac/Linux

pytest
```

Tests use in-memory SQLite and a mocked LLM — **no Ollama or database needed**.

Expected output:
```
collected 40+ items
test_health.py ....
test_sessions.py .........
test_chat.py ........
test_artifacts.py .......
test_crud.py ..........
test_retrieval.py ......
test_skills.py ..........
== X passed in X.Xs ==
```

---

## Using Cloud LLMs Instead of Ollama

If you prefer Anthropic Claude or OpenAI, edit your `.env`:

```bash
# Anthropic Claude (recommended for best quality)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-actual-key

# OpenAI GPT-4o
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key
```

Restart the backend (`Ctrl+C` then `python run.py`). The model badge in the UI will update automatically.

You don't need Ollama running when using a cloud provider.

---

## API Explorer

Once the backend is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You can test all API endpoints directly from the browser.

---

## Stopping Everything

```bash
# In each terminal, press:
Ctrl + C
```

The SQLite database (`backend/lenny_demo.db`) and ChromaDB index (`backend/chroma_db/`) persist between restarts — you don't need to re-index transcripts every time.
