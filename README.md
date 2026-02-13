# Repo Doc Bot

Repo Doc Bot is a backend-driven system that allows users to **ingest a GitHub repository** and **ask natural-language questions about its codebase**.
It uses **retrieval-augmented generation (RAG)** to ground answers in real code and markup extracted from the repository.

This project was built as a **capstone submission**, with a strong focus on **correctness, architectural clarity, and real-world design trade-offs**, rather than feature bloat.

---

## ✨ Key Features

* Ingest any public GitHub repository
* Index the entire codebase locally
* Structural chunking for Python and HTML
* Vector-based retrieval using Qdrant vector database
* Natural-language Q&A grounded in retrieved files
* Clean, ChatGPT-style UI (ingest → chat)
* End-to-end system tests

---

## 🧠 Architecture Overview

The system follows a classic **RAG pipeline**:

```
Repository → Chunking → Embeddings → Vector Store
                                   ↓
User Query → Query Embedding → Retrieval → LLM Answer
```

### Ingestion

* Full `git clone` of the target repository
* File-type filtering:

  * `.py`, `.html`, `.js`, `.md`, `.txt`
* Ignored directories:

  * `.git/`, `node_modules/`, `venv/`, `__pycache__/`
* Repository is deleted after indexing

Only **repo-relative paths** are stored (no local filesystem leakage).

---

## 🧩 Structural Chunking (MVP+2)

### Python (`.py`)

Python files are chunked using **AST-based structural parsing** in a single pass, preserving OOP hierarchy:

Chunk priority order:

1. Module docstring
2. Imports (grouped)
3. Classes (entire class body)
4. Top-level functions (not inside classes)
5. Remaining top-level code

Each line of code belongs to **exactly one chunk**. Oversized chunks fall back to blind chunking.

---

### HTML (`.html`)

HTML files are chunked using **semantic DOM structure**:

* `<main>` dominates and is chunked as a single unit (if present)
* Otherwise, the following tags are chunked as complete subtrees:

  * `<section>`, `<article>`, `<nav>`, `<form>`, `<header>`, `<footer>`
* `<div>` is intentionally not treated as a chunk
* Remaining content is grouped into a single fallback chunk

This mirrors how humans reason about page structure while avoiding noisy container tags.

---

### Other Files

* JavaScript, Markdown, and text files use **blind chunking with overlap**
* Blind chunking is also used as a fallback for oversized or invalid structured chunks

---

## 🔍 Retrieval & Answering

* Queries are embedded using Ollama (`nomic-embed-text`)
* Retrieval uses brute-force cosine similarity over stored vectors
* Top-K chunks are injected into the LLM prompt as context

The LLM is instructed to answer **based on retrieved context**, avoiding hallucination when information is missing.

---

## 💬 Conversational Behavior (Design Decision)

The system currently implements **single-turn RAG**:

* Each query is handled independently
* No persistent chat history is stored by default

This is a **conscious design choice** to prioritize correctness and grounding over conversational fluency.

Conversational continuity (e.g. resolving references like "they") can be introduced by **contextualizing the query text before embedding** (lightweight conversational RAG). Full chat memory is intentionally deferred as a post-submission enhancement.

---

## 🖥️ Tech Stack

* **Backend**: FastAPI
* **Frontend**: Vanilla HTML, CSS, React,JavaScript
* **Vector Store**: Qdrant (open-source vector database for storing embeddings)
* **Embeddings**: Ollama (`nomic-embed-text`)
* **LLM**: Groq (primary), Ollama fallback
* **Parsing**: Python `ast`, BeautifulSoup
* **Testing**: pytest (system-level tests)

---

## 📁 Project Structure

```
repo-doc-bot/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── infra/
│   │   ├── llm.py
│   │   └── db.py
│   └── tasks/
│       ├── ingest/
│       │   ├── ingest.py
│       │   ├── repo_clone/
│       │   ├── embedding/
│       │   │   ├── embedding_blind.py
│       │   │   ├── embedding_python.py
│       │   │   ├── embedding_html.py
│       │   │   └── dispatcher.py
│       │   └── vector_store/
│       └── query/
│           ├── query.py
│           ├── rag/
│           └── answer/
│
├── frontend/
│   ├── ingest.html
│   ├── chat.html
│   ├── styles.css
│   ├── ingest.js
│   └── chat.js
│
├── tests/
│   ├── test_ingest.py
│   └── test_query.py
│
├── pytest.ini
├── requirements.txt
├── .env (not committed)
└── README.md
```

---

## 🚀 Running the Project

### Prerequisites

* Python 3.11+
* Docker (for running Qdrant)
* Ollama installed and running
* Git

### Setup

**1. Start Qdrant (using Docker):**

```bash
docker run -p 6333:6333 qdrant/qdrant
```

This starts the Qdrant vector database on `localhost:6333`.

**2. Install Python dependencies:**

```bash
pip install -r requirements.txt
```

**3. Create a `.env` file:**

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=code_embeddings
GROQ_API_KEY=your_key_here
```

**4. Start the backend:**

```bash
uvicorn backend.main:app --reload
```

Open in browser:

```
http://localhost:8000
```

---
🌐 Running the  Frontend 

Go to the frontend folder

```bash
cd frontend

```
Install dependencies:
```bash
npm install

```
⚙️ Frontend Environment Configuration

Create a config.js file inside the src directory:
```bash
src/config.js
```

Add the backend URL-
```bash
API_URL="BACKEND_URL"
```
▶️ Start the Frontend

Run:
```bash
npm start

```
The frontend will start at:
```bash
http://localhost:3000/

```
---

## 🧪 Running Tests

Make sure Qdrant and Ollama are running.

```bash
pytest
```

Tests are **end-to-end system tests** that validate:

* Repository ingestion
* Vector indexing
* Retrieval
* LLM-based answering

---

## 📌 Project Status

* ✅ MVP complete
* ✅ MVP+1 (UI + tests) complete
* ✅ MVP+2 (structural chunking) complete for .py and .html

The project is **submission-ready** in its current form.

---

## 📄 License

This project was developed for academic purposes as part of a capstone submission.