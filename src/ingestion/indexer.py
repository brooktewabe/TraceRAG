import json
from pathlib import Path
from typing import Dict, Any, List
import chromadb
from chromadb.utils import embedding_functions

from src.config import settings
from src.core.models import DocumentRecord


class DocumentIndexer:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL_NAME
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": settings.DISTANCE_METRIC}
        )

    def load_documents_from_json(self, file_path: Path = None) -> List[DocumentRecord]:
        path = file_path or settings.DATA_PATH
        if not path.exists():
            raise FileNotFoundError(f"Source documents file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        return [DocumentRecord(**item) for item in raw_data]

    def index_documents(self, documents: List[DocumentRecord]) -> Dict[str, Any]:
        """
        Idempotent batch upsert into Chroma vector store.
        """
        if not documents:
            return {"status": "no_op", "indexed_count": 0}

        ids = [doc.id for doc in documents]
        texts = [doc.content for doc in documents]
        metadatas = [
            {
                "title": doc.title,
                "department": doc.department,
                "category": doc.category,
                "access_level": doc.access_level,
                "updated_at": doc.updated_at or "",
            }
            for doc in documents
        ]

        # Upsert ensures existing IDs are updated rather than duplicated
        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

        return {
            "status": "success",
            "indexed_count": len(documents),
            "total_collection_count": self.collection.count()
        }

    def run_full_sync(self) -> Dict[str, Any]:
        docs = self.load_documents_from_json()
        return self.index_documents(docs)


if __name__ == "__main__":
    indexer = DocumentIndexer()
    res = indexer.run_full_sync()
    print("Ingestion Result:", res)

