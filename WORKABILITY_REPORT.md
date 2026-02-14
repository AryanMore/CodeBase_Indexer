# Workability Report

## Verdict
**Yes — after basic setup of Qdrant and Ollama, the core app flow should work.**

What was failing in this environment was not an internal logic crash, but missing runtime services.

## Evidence

### Backend
- `pytest -q` result: 4 tests passed, 2 failed.
- Failing tests:
  - `tests/test_ingest.py::test_ingest_repo` failed with Qdrant connection refusal (`localhost:6333`).
  - `tests/test_query.py::test_query_repo` failed with Ollama connection error.
- Why this happens:
  - Backend Qdrant client defaults to `QDRANT_HOST=localhost` and `QDRANT_PORT=6333`.
  - Embeddings and chat use Ollama directly.

### Frontend
- `npm run build` failed initially because dependencies were not installed (`react-scripts: not found`).
- `npm ci` failed because lockfile mismatch (`Missing: yaml@2.8.2 from lock file`), which affects deterministic CI installs.
- In practice, for local usage this is usually resolved by `npm install` (which updates lockfile), then build/run.

## What must be true for it to work
1. Qdrant is running (for example via Docker on port 6333).
2. Ollama is installed and running locally.
3. Frontend dependencies are installed; ideally lockfile is synced and committed for reproducible installs.

## Bottom line
- **Backend:** expected to work once Qdrant + Ollama are up.
- **Frontend:** expected to work after installing dependencies; but lockfile sync should be fixed for clean `npm ci` workflows.
