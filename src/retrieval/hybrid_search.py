import re
from typing import List, Dict, Any
from src.core.models import SearchResult
from src.ingestion.indexer import DocumentIndexer
from src.core.security import is_authorized


class KeywordSearchBaseline:
    """
    Keyword/lexical search baseline using term-frequency matching.
    Used for benchmarking semantic search vs keyword-only legacy search.
    """
    def __init__(self):
        indexer = DocumentIndexer()
        self.documents = indexer.load_documents_from_json()

    def search(
        self,
        query: str,
        user_role: str = "all_employees",
        top_k: int = 3
    ) -> List[SearchResult]:
        query_terms = set(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return []

        scored_docs = []
        for doc in self.documents:
            if not is_authorized(user_role, doc.access_level):
                continue

            doc_text = f"{doc.title} {doc.content}".lower()
            doc_terms = re.findall(r"\w+", doc_text)
            term_matches = sum(1 for term in query_terms if term in doc_terms)

            if term_matches > 0:
                score = term_matches / len(query_terms)
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)

        results: List[SearchResult] = []
        for score, doc in scored_docs[:top_k]:
            results.append(
                SearchResult(
                    id=doc.id,
                    title=doc.title,
                    department=doc.department,
                    category=doc.category,
                    access_level=doc.access_level,
                    distance=round(1.0 - score, 4),
                    relevance_score=round(score, 4),
                    content=doc.content
                )
            )

        return results

