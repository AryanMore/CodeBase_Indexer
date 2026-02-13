# Repository Health Report

## Verdict
The repository is **not runnable out-of-the-box** in this environment without additional setup/fixes.

## Blocking issues found

1. `backend/infra/llm.py` imports `groq` at module import time.
2. `requirements.txt` does not include `groq`, so backend import/test collection fails.
3. Backend config defaults to `USE_GROQ = True`, requiring `GROQ_API_KEY`.
4. Tests are integration-style and require external services (Qdrant + Ollama) and outbound network.
5. Frontend depends on a manually created `frontend/src/config.js` file; it is not versioned.
6. Frontend install/test flow is currently inconsistent in this environment (`react-scripts` unavailable after attempted install).

## What is needed for it to work

- Add and install the missing `groq` Python dependency.
- Provide `.env` with `GROQ_API_KEY` (or set `USE_GROQ=False` and ensure Ollama model availability).
- Start Qdrant and Ollama before running tests/backend.
- Add `frontend/src/config.js` with `API_URL` export or adjust frontend config strategy.
- Resolve npm lock/dependency consistency for repeatable frontend setup.

## Commands used

- `pytest -q`
- `pip install -r requirements.txt`
- `cd frontend && npm test -- --watchAll=false`
- `cd frontend && npm ci`
- `cd frontend && npm install`
