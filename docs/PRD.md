# Product Requirements Document
## The Lenny Growth Assistant

**Version:** 1.0  
**Date:** September 2026  
**Author:** Forward Deployment Engineer Candidate

---

## 1. Forward Deployment Discovery Brief

### 1.1 User and Problem

**Primary user:** Product managers and growth practitioners at early-to-mid stage tech companies.

**Job to be done:** The user needs to quickly access proven product and growth frameworks from Lenny's interviews without spending hours searching through transcript archives. They want grounded, practitioner-quality answers — not generic LLM-generated advice they can't trust.

**Pain removed:**
- Hours wasted searching across 400+ podcast episodes for a specific framework or insight
- Distrust of generic AI answers that can't be traced to a credible source
- Writing friction: converting research into shareable content requires additional effort
- No reusable outputs — current workflow produces knowledge that lives in Slack threads or personal notes, not team-accessible artifacts

### 1.2 Success Metrics

**Primary metric:** Grounding rate — the percentage of responses that contain at least one cited source from the transcript knowledge base. Target: ≥ 85% of non-trivially-answerable questions cite at least one transcript.

**Secondary metrics:**
- Session return rate: % of users who start a second session within 7 days
- Artifact generation rate: % of sessions that produce at least one artifact (indicates team utility beyond personal Q&A)
- Time-to-first-answer: < 15 seconds for Ollama local, < 5 seconds for cloud providers

**Operational metric:** Zero silent failures — every LLM unavailability, retrieval miss, or DB error must surface a structured log entry and a user-visible error message.

### 1.3 Assumptions

1. **Transcript availability:** The transcript repository contains sufficient coverage of the major product and growth topics users will ask about. The demo ships with 3 sample transcripts; a production deployment would ingest the full archive.
2. **Ollama hardware:** The evaluator's machine can run `llama3.2` (3B parameter model) comfortably. Response quality will be lower than Claude but functional for demonstrating the system.
3. **Single user:** This v1 is designed for individual or small-team use. There is no authentication layer; sessions are distinguishable by ID but not by user identity.
4. **Transcript licensing:** Lenny's transcripts are publicly available. The system uses them as a knowledge base without redistribution; transcripts are stored locally and never transmitted to third parties.
5. **PostgreSQL availability:** The evaluator either uses Docker Compose (which starts Postgres automatically) or has a local PostgreSQL instance.
6. **No streaming required for v1:** The LLM response is returned as a complete message after generation. Streaming would improve perceived latency but is not required for correctness.

### 1.4 Scope Choices

**Included:**
- Full RAG pipeline with source citations
- Three distinct skills (conversational Q&A, Ship 30 essay, artifact generation)
- Markdown and HTML artifact rendering with security isolation
- Session persistence and message history
- LLM provider toggle (Ollama / Anthropic / OpenAI) via environment variable
- Docker Compose one-command setup
- Automated test suite (unit + integration)

**Intentionally excluded:**
- **Authentication / multi-user:** Out of scope for an internal demo tool. Would add OAuth or API key auth before production.
- **Streaming responses:** Adds frontend complexity (SSE or WebSockets) disproportionate to the demo value. Noted as a clear next step.
- **Transcript auto-refresh / scheduled ingestion:** Ingestion is triggered manually. A production system would watch for new transcripts or run nightly.
- **Vector store clustering / reranking:** A cross-encoder reranker would improve retrieval quality. Excluded to keep dependencies minimal for local demo.
- **Mobile-first design:** Responsive breakpoints exist but the primary experience targets desktop (1280px+).

### 1.5 Risks and Trade-offs

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| **Hallucination** — LLM generates plausible but unsupported claims | Medium | High | System prompt instructs strict grounding; citations make it auditable; model is prompted to say "I don't have coverage" when context is empty |
| **Local model quality** — Ollama/llama3.2 is weaker than Claude | High | Medium | UI prominently shows active model; README sets expectations; provider switch is one env var |
| **Latency** — Ollama on consumer hardware can take 20-40s | High | Medium | Loading state in UI; no timeout until 120s; documented in README |
| **Retrieval misses** — relevant transcript not retrieved if query phrasing differs from chunk phrasing | Medium | Medium | Top-5 retrieval; cosine similarity with normalized embeddings; ingestion produces overlapping chunks |
| **Artifact HTML injection** | Low | High | Sandboxed iframe (no `allow-scripts`), CSP meta tag injected, DOMPurify for Markdown; documented in `ArtifactViewer.tsx` |
| **Database unavailability** | Low | High | Graceful error response; `/api/v1/ready` shows `degraded` status; structured logs |
| **Transcript data leakage** | Low | Low | Transcripts stored locally; never transmitted to third parties unless using cloud LLM (user's own API key) |
| **Cost overrun (cloud LLM)** | Low | Medium | Each request uses ~2,000-4,000 tokens; documented; Ollama default avoids cloud cost entirely |

---

## 2. User Flows

### 2.1 Core Q&A Flow
```
User opens app
  → Creates new session (optional title)
  → Selects "Ask Lenny" skill (default)
  → Types question
  → System retrieves top-5 transcript chunks
  → LLM generates grounded answer with inline citations
  → Sources displayed (expandable)
  → User asks follow-up (session context maintained)
```

### 2.2 Ship 30 Essay Flow
```
User selects "Ship 30 Essay" skill
  → Types topic (e.g., "retention-driven growth")
  → System retrieves relevant transcript chunks
  → LLM generates ~1,250-word essay in Ship 30 format
  → Essay displayed in chat bubble with Markdown rendering
  → User copies or requests artifact version
```

### 2.3 Artifact Generation Flow
```
User selects "Markdown Doc" or "HTML Page" skill
  → Types instructions
  → System retrieves context + uses session history
  → LLM generates artifact
  → Artifact Viewer opens beside chat
  → User reads, copies, or downloads
  → Viewer can be closed; artifact persisted in DB
```

---

## 3. Acceptance Criteria

| Feature | Acceptance Criterion |
|---------|---------------------|
| RAG Q&A | Response includes ≥ 1 cited source when transcript coverage exists |
| Source citations | Each source shows episode name, relevance score, and excerpt |
| Session persistence | Messages survive page refresh |
| Multi-turn context | Follow-up questions reference prior turns without repeating context |
| Ship 30 essay | Output is 1,100–1,400 words with H2 headings, bullets, bold, and a takeaway |
| Markdown artifact | Rendered in artifact viewer with proper heading/list/code formatting |
| HTML artifact | Rendered in sandboxed iframe; CSP blocks scripts; CSS renders correctly |
| LLM toggle | Changing `LLM_PROVIDER` + restart switches provider with no code changes |
| Provider badge | Active model visible in UI header at all times |
| Error handling | LLM unavailable → user-visible error message; not a 500 crash |
| Empty retrieval | "I don't have transcript coverage" message, not a hallucinated answer |
| One-command start | `docker-compose up` starts DB + backend + frontend successfully |
| Tests pass | `pytest` runs without a live DB or LLM |

---

## 4. Implementation Plan

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | Project scaffold, config, .env | ✅ Done |
| 2 | FastAPI backend, DB models, health endpoints | ✅ Done |
| 3 | LLM client abstraction (Ollama/Anthropic/OpenAI) | ✅ Done |
| 4 | Ingestion pipeline + ChromaDB | ✅ Done |
| 5 | RAG retrieval + agent runner | ✅ Done |
| 6 | Ship 30 + artifact skills | ✅ Done |
| 7 | React frontend + artifact viewer | ✅ Done |
| 8 | Docker Compose + Nginx | ✅ Done |
| 9 | Tests (unit + integration) | ✅ Done |
| 10 | Documentation | ✅ Done |
