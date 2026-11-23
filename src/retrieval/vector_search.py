from typing import List, Optional
import chromadb
from chromadb.utils import embedding_functions

from src.config import settings
from src.core.models import SearchResult
from src.core.security import is_authorized


class VectorSearchEngine:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL_NAME
        )
        self.collection = self.client.get_collection(
            name=settings.COLLECTION_NAME,
            embedding_function=self.embedding_fn
        )

    def search(
        self,
        query: str,
        department: Optional[str] = None,
        user_role: str = "all_employees",
        top_k: int = 3,
        threshold: Optional[float] = None
    ) -> List[SearchResult]:
        if not query.strip():
            return []

        # Build metadata filter if department is specified
        where_filter = None
        if department and department.strip():
            where_filter = {"department": department.strip()}

        # Query vector store (retrieving a few extra candidates to allow post-security filtering)
        fetch_k = min(top_k * 2, 10)
        results = self.collection.query(
            query_texts=[query],
            n_results=fetch_k,
            where=where_filter
        )

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]
        ids = results["ids"][0]

        applied_threshold = threshold if threshold is not None else settings.RELEVANCE_DISTANCE_THRESHOLD
        valid_results: List[SearchResult] = []

        for doc_id, text, meta, dist in zip(ids, docs, metas, dists):
            # 1. Distance threshold guardrail
            if dist > applied_threshold:
                continue

            # 2. Role-Based Access Control check
            doc_access = meta.get("access_level", "all_employees")
            if not is_authorized(user_role, doc_access):
                continue

            similarity = max(0.0, min(1.0, 1.0 - dist))

            valid_results.append(
                SearchResult(
                    id=doc_id,
                    title=meta.get("title", "Untitled"),
                    department=meta.get("department", "General"),
                    category=meta.get("category", "General"),
                    access_level=doc_access,
                    distance=round(dist, 4),
                    relevance_score=round(similarity, 4),
                    content=text
                )
            )

            if len(valid_results) >= top_k:
                break

        return valid_results

    def get_document_by_id(self, doc_id: str, user_role: str = "all_employees") -> Optional[SearchResult]:
        res = self.collection.get(ids=[doc_id])
        if not res["documents"]:
            return None

        meta = res["metadatas"][0]
        doc_access = meta.get("access_level", "all_employees")
        if not is_authorized(user_role, doc_access):
            return None

        return SearchResult(
            id=doc_id,
            title=meta.get("title", "Untitled"),
            department=meta.get("department", "General"),
            category=meta.get("category", "General"),
            access_level=doc_access,
            distance=0.0,
            relevance_score=1.0,
            content=res["documents"][0]
        )

    def list_departments(self) -> List[str]:
        all_data = self.collection.get()
        depts = {m.get("department") for m in all_data["metadatas"] if m.get("department")}
        return sorted(list(depts))

