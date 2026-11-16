"""
Phase 2 — Step 1: Ingest documents into a persistent Chroma database.

The Learning Rule:
  1. What goes in?
     - Documents (text strings)
     - Unique IDs (strings)
     - Metadata dictionaries (department, category, access_level, title)
  2. What happens internally?
     - Chroma uses Sentence Transformers to compute 384-d vectors for each document.
     - Chroma writes document text & metadata to an SQLite table (`chroma.sqlite3`).
     - Chroma builds and saves an HNSW graph index to disk inside `chroma_data/`.
  3. What comes out?
     - A persistent vector store on disk ready for sub-millisecond queries.

Run:
    python step1_ingest_chroma.py
"""

from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

from documents_with_metadata import DOCUMENTS

# ------------------------------------------------------------------
# 1. Setup Persistent Storage & Embedding Function
# ------------------------------------------------------------------
# Define where Chroma should save its database on disk
DB_DIR = Path(__file__).resolve().parent.parent / "chroma_data"
print(f"Target Chroma storage path: {DB_DIR}")

# PersistentClient writes to disk (unlike EphemeralClient / Client() which is RAM-only)
client = chromadb.PersistentClient(path=str(DB_DIR))

# Choose the embedding model.
# By passing this to Chroma, Chroma automatically embeds documents during ingestion
# and automatically embeds queries during search using the exact same model!
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ------------------------------------------------------------------
# 2. Create or Get Collection
# ------------------------------------------------------------------
# A 'Collection' in Chroma is like a Table in SQL or an Index in Elasticsearch.
# We set hnsw:space to "cosine" so distance = (1 - cosine_similarity).
# - Distance 0.0 means identical meaning.
# - Lower distance = better match!
collection = client.get_or_create_collection(
    name="company_knowledge_base",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

print(f"Existing document count before ingestion: {collection.count()}")

# ------------------------------------------------------------------
# 3. Prepare Batch Data for Ingestion
# ------------------------------------------------------------------
ids = [doc["id"] for doc in DOCUMENTS]
documents = [doc["content"] for doc in DOCUMENTS]
metadatas = [
    {
        "title": doc["title"],
        "department": doc["department"],
        "category": doc["category"],
        "access_level": doc["access_level"],
    }
    for doc in DOCUMENTS
]

# ------------------------------------------------------------------
# 4. Upsert into Chroma
# ------------------------------------------------------------------
# upsert: if the ID already exists, it updates it; if not, it inserts it.
# This makes the script idempotent (safe to run multiple times without duplicating data).
print(f"Upserting {len(documents)} documents into Chroma...")
collection.upsert(
    ids=ids,
    documents=documents,
    metadatas=metadatas
)

print(f"Ingestion complete! Total documents in collection: {collection.count()}")
print("All vectors and metadata are now saved to disk in `chroma_data/`.\n")

