# Agent Transcripts

This folder contains logs from the coding agent sessions used to build this project.

## Contents

| File | Description |
|------|-------------|
| `session-01-scaffold.md` | Initial project scaffold, directory structure, base config |
| `session-02-backend.md` | FastAPI backend, DB models, CRUD, LLM client |
| `session-03-rag.md` | Ingestion pipeline, ChromaDB, RAG retrieval |
| `session-04-skills.md` | Ship 30 skill, artifact skill, agent runner |
| `session-05-frontend.md` | React frontend, artifact viewer, TypeScript fixes |
| `session-06-infra.md` | Docker Compose, Nginx, tests, documentation |

## Notes

- All API keys and secrets have been removed before committing
- Failed attempts and corrections are preserved in each session log
- The TypeScript fix for unused `onOpenArtifact` prop is documented in `session-05`
- The `create-vite` interactive prompt workaround (manual file scaffold) is in `session-05`

## Key decisions logged

1. **Manual frontend scaffold** — `npm create vite` requires interactive prompt confirmation on Windows PowerShell; scaffolded manually instead of fighting the CLI
2. **SQLite for tests** — switched from mocking the entire DB layer to using `aiosqlite` in-memory; cleaner tests that actually exercise the CRUD logic
3. **`allow-same-origin` iframe sandbox** — initial approach used `allow-scripts` for CSS; corrected to block scripts entirely and verified CSS still renders without `allow-scripts`
4. **Chunk ID strategy** — first attempt used `f"{filename}_{index}"` as IDs; changed to SHA256 hash to avoid ChromaDB rejecting IDs with special characters from filenames
