import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from src.config import settings
from src.core.models import (
    SearchRequest,
    SearchResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from src.retrieval.vector_search import VectorSearchEngine
from src.workflows.agent import ask_knowledge_agent
from src.ingestion.indexer import DocumentIndexer

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Enterprise Knowledge & Semantic Search Platform API."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

search_engine = VectorSearchEngine()
indexer = DocumentIndexer()


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    try:
        count = search_engine.collection.count()
        return {
            "status": "healthy",
            "version": settings.API_VERSION,
            "indexed_documents": count,
            "embedding_model": settings.EMBEDDING_MODEL_NAME
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector store unreachable: {str(e)}"
        )


@app.get("/api/v1/departments", response_model=List[str], tags=["Discovery"])
def list_departments() -> List[str]:
    return search_engine.list_departments()


@app.post("/api/v1/search", response_model=SearchResponse, tags=["Search"])
def search_documents(request: SearchRequest) -> SearchResponse:
    results = search_engine.search(
        query=request.query,
        department=request.department,
        user_role=request.user_role,
        top_k=request.top_k
    )
    return SearchResponse(
        query=request.query,
        total_found=len(results),
        results=results
    )


@app.post("/api/v1/rag/query", response_model=RAGQueryResponse, tags=["RAG"])
def query_rag_agent(request: RAGQueryRequest) -> RAGQueryResponse:
    try:
        response = ask_knowledge_agent(
            query=request.query,
            department=request.department,
            user_role=request.user_role
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG workflow execution failed: {str(e)}"
        )


@app.post("/api/v1/ingest/sync", tags=["Ingestion"])
def sync_documents() -> Dict[str, Any]:
    try:
        res = indexer.run_full_sync()
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
