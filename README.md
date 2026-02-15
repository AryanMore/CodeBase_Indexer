# Codebase Indexer

### A Policy-Driven Code Reasoning Engine

Codebase Indexer is a backend-frontend system for **structured understanding and reasoning over entire software repositories**.

Unlike basic retrieval-augmented systems that rely on flat chunking, this project explores **policy-governed context expansion**, **semantic chunking**, and **controlled agentic retrieval** for accurate code comprehension.

The goal is not to replicate Cursor-style file mutation, but to investigate how repository information can be **stored, structured, retrieved, and expanded safely and systematically**.

---

## Core Idea

Most RAG systems treat source code as text.

Codebase Indexer treats it as **structured data with relationships**, enabling:

* Semantic chunking (AST / DOM / Tree-Sitter based)
* Relationship-aware expansion
* Budget-constrained context growth
* Rulebook-governed retrieval behavior
* JSON-validated LLM orchestration

The focus is on **how information is modeled and accessed**, not on editing or mutating files.

---

## System Overview

The system consists of:

* **Backend**: FastAPI (Python)
* **Frontend**: React
* **Vector Store**: Qdrant
* **Embeddings**: Ollama (`nomic-embed-text`)
* **LLM**:

  * Primary: Groq (`llama3.2-8b-instant`)
  * Fallback: Local Ollama (`llama3.2-3b`)

Users can:

1. Ingest a public GitHub repository
2. Query the indexed repository via chat
3. Toggle policy-driven expansion on or off

---

## Ingestion Pipeline

### 1. Repository Clone

The system clones the provided GitHub repository locally.

### 2. Language-Aware Semantic Chunking

Supported languages:

* Python → AST parsing
* JavaScript → Tree-Sitter
* HTML → BeautifulSoup (DOM structure)

All other file types use blind chunking with overlap.

For supported languages, chunks are structured into semantic types such as:

* Functions
* Classes
* Imports
* Top-level code
* DOM sections

Chunk formats and metadata are defined in JSON policy files (e.g., `python.json`).
This enables runtime modification of supported relationships without altering core dispatcher logic.

### 3. Relationship Encoding

Chunks may include metadata fields such as:

* `identifier`
* `uses`
* `member_functions`
* `file_scope`

These are stored strictly as metadata to allow rule-driven expansion during retrieval.

### 4. Embedding & Storage

Chunks are embedded using:

```
nomic-embed-text (Ollama)
```

Vectors are stored in Qdrant along with structured metadata.

---

## Retrieval & Policy-Driven Expansion

After ingestion, users interact via a chat interface.

The system operates in two modes:

* Standard RAG
* Expansion Agent Mode (default)

---

### Controlled Expansion Architecture

Instead of blindly retrieving Top-K chunks, the system introduces:

* A **rulebook per language**
* A **budget counter**
* A **depth counter**
* Strict **JSON-only LLM outputs**

Each chunk type defines:

* Whether expansion is allowed
* Which relationships may be followed
* Cost of each expansion

Example expansion rules:

* Expand via `file_scope` (cost: 0)
* Expand via `uses` (cost: 1)

The LLM must respond in structured JSON:

```json
{
  "action": "answer"
}
```

or

```json
{
  "action": "request-expansion",
  "rule": "...",
  "target_chunk": "...",
  "identifier": "..."
}
```

The orchestrator validates:

* Rule legality
* Budget availability
* Depth limits
* Format correctness

Only valid expansions are executed.

This prevents:

* Unlimited context growth
* Greedy expansion loops
* Tunnel-vision over a single symbol
* Invalid relationship traversal

If constraints are violated, the model is forced to correct its output.

---

## Context Stitching

If a semantic block (e.g., large function) was split due to size:

* Retrieval automatically reconstructs and orders all related chunks
* The LLM receives a complete logical unit

This ensures semantic integrity even under size constraints.

---

## Conversational Behavior

* Chat sessions persist during active use
* Sessions are memory-based (not stored permanently)
* Closing the session resets state
* No long-term conversation history is retained

---

## Design Principles

* Structure over plain text
* Policy-driven retrieval
* Explicit expansion control
* Runtime language extensibility
* Deterministic orchestration around non-deterministic models

---

## Setup Instructions

### Prerequisites

* Python 3.10+
* Node.js
* Docker
* Ollama installed and running

---

### 1. Start Qdrant (Docker)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

---

### 2. Create `.env` file

```
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=code_embeddings
USE_GROQ=true
GROQ_API_KEY=<your_key>
```

---

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

### 5. Start Backend

```bash
uvicorn backend.main:app --reload
```

---

### 6. Start Frontend

```bash
npm start
```

Frontend runs on:

```
http://localhost:3000
```

Backend runs on:

```
http://localhost:8000
```

---

## Current Scope

* Repository ingestion
* Semantic chunking for Python, JS, HTML
* Rule-governed expansion agent
* Budget-controlled recursive retrieval
* Dual LLM backend (Groq + local fallback)
* Session-scoped conversational memory

---

## Out of Scope

* File editing or mutation
* Automatic code patching
* Long-term chat persistence
* Enterprise-grade security hardening

---

## Motivation

This project explores how large codebases can be:

* Structured
* Indexed
* Queried
* Expanded
* Reasoned about

under explicit, enforceable retrieval policies.

It serves as a foundation for future work in controlled agentic code intelligence systems.
