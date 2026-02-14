
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.tasks.ingest.ingest import ingest
from backend.tasks.query.query import query_repo
from backend.infra.db import get_qdrant_client, get_collection_name
from backend.tasks.query.rag.agent_rag import retrieve_chunks_for_agent, expand_context_for_agent
from AI_Agent.app import run_agent


app = FastAPI(title="Repo Doc Bot")


# ---------------- CORS (For React) ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- MODELS ----------------

class IngestRequest(BaseModel):
    repo_url: str


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


class RagRetrieveRequest(BaseModel):
    repo_url: Optional[str] = None
    query: str
    top_k: int = 5


class RagExpandRequest(BaseModel):
    repo_url: Optional[str] = None
    source_chunk_ids: List[str]
    requested_code_types: List[str]
    scope: str = "same_file"
    max_chunks: int = 3


class AgentQueryRequest(BaseModel):
    repo_url: str
    question: str
    session_id: Optional[str] = None


class AgentQueryResponse(BaseModel):
    answer: str
    session_id: str

# ---------------- ROUTES ----------------


@app.get("/")
def root():
    return {"message": "Backend is running"}


@app.get("/has_index")
def has_index():

    client = get_qdrant_client()
    collection_name = get_collection_name()

    try:
        info = client.get_collection(collection_name)
        count = info.points_count
        return {"has_index": count > 0}

    except:
        return {"has_index": False}


@app.post("/ingest")
def ingest_repo(request: IngestRequest):

    ingest(request.repo_url)

    return {"status": "success"}


@app.post("/query", response_model=QueryResponse)
def query_repository(request: QueryRequest):

    answer = query_repo(request.question)

    return {"answer": answer}


@app.post("/rag/retrieve")
def rag_retrieve(request: RagRetrieveRequest):
    chunks = retrieve_chunks_for_agent(
        query=request.query,
        top_k=request.top_k,
        repo_url=request.repo_url,
    )
    return {"chunks": chunks}


@app.post("/rag/expand")
def rag_expand(request: RagExpandRequest):
    chunks = expand_context_for_agent(
        repo_url=request.repo_url,
        source_chunk_ids=request.source_chunk_ids,
        requested_code_types=request.requested_code_types,
        scope=request.scope,
        max_chunks=request.max_chunks,
    )
    return {"chunks": chunks}


@app.post("/agent/query", response_model=AgentQueryResponse)
def agent_query(request: AgentQueryRequest):
    state = run_agent(
        user_query=request.question,
        repo_url=request.repo_url,
        session_id=request.session_id,
    )

    return {
        "answer": state.get("explanation") or "",
        "session_id": state.get("session_id") or (request.session_id or ""),
    }
