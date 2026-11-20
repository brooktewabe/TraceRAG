from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    title: str
    department: str
    category: str
    access_level: str = "all_employees"
    updated_at: Optional[str] = None


class DocumentRecord(BaseModel):
    id: str
    title: str
    department: str
    category: str
    access_level: str = "all_employees"
    updated_at: Optional[str] = None
    content: str


class SearchResult(BaseModel):
    id: str
    title: str
    department: str
    category: str
    access_level: str
    distance: float
    relevance_score: float = Field(..., description="Estimated similarity score (0.0 to 1.0)")
    content: str


class SearchRequest(BaseModel):
    query: str
    department: Optional[str] = None
    user_role: str = "all_employees"
    top_k: int = 3


class SearchResponse(BaseModel):
    query: str
    total_found: int
    results: List[SearchResult]


class RAGQueryRequest(BaseModel):
    query: str
    department: Optional[str] = None
    user_role: str = "all_employees"
    allow_rewrites: bool = True


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    abstained: bool
    confidence_score: float
    sources: List[str]
    decision_trace: List[str]

