
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.tasks.ingest.ingest import ingest
from backend.tasks.query.query import query_repo
from backend.infra.db import get_qdrant_client, get_collection_name


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
