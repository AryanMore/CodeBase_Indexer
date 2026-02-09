from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.tasks.ingest.ingest import ingest
from backend.tasks.query.query import query_repo
from backend.infra.db import get_qdrant_client, get_collection_name


app = FastAPI(title="Repo Doc Bot")


class IngestRequest(BaseModel):
    repo_url: str


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "ingest.html")


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



@app.post("/query")
def query_repository(request: QueryRequest):
    answer = query_repo(request.question)
    return {"answer": answer}


@app.get("/chat")
def serve_chat():
    return FileResponse(FRONTEND_DIR / "chat.html")
