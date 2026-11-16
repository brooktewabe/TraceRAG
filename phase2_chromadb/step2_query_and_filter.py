"""
Phase 2 — Step 2: Query Chroma & use Metadata Filters.

The Learning Rule:
  1. What goes in?
     - A plain query string (e.g. "Reset password")
     - Optional metadata filter (e.g. where={"department": "IT"})
     - n_results (top K documents to retrieve)
  2. What happens internally?
     - Chroma embeds the query string using the collection's embedding function.
     - If a `where` filter is provided, Chroma filters candidates by metadata first.
     - Chroma searches the HNSW graph to find the nearest vectors.
  3. What comes out?
     - A dictionary containing:
         - documents: matching text chunks
         - metadatas: associated metadata (department, title, etc.)
         - distances: cosine distances (where 0.0 = identical, lower is better)

Run:
    python step2_query_and_filter.py
"""

from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

# ------------------------------------------------------------------
# 1. Connect to the Existing Persistent Database
# ------------------------------------------------------------------
DB_DIR = Path(__file__).resolve().parent.parent / "chroma_data"
client = chromadb.PersistentClient(path=str(DB_DIR))

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Connect to the existing collection (no re-ingestion needed!)
collection = client.get_collection(
    name="company_knowledge_base",
    embedding_function=embedding_fn
)

print(f"Connected to Chroma. Total indexed documents: {collection.count()}\n")


def print_search_results(header: str, results: dict) -> None:
    print(header)
    print("-" * 65)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), start=1):
        # In cosine space: similarity ≈ 1 - distance
        similarity = 1.0 - dist
        print(f"  #{rank}  Distance: {dist:.4f}  (Est. Similarity: {similarity:.4f})")
        print(f"      Title:      {meta['title']} [{meta['department']}]")
        print(f"      Snippet:    {doc[:110]}...")
    print()


# ------------------------------------------------------------------
# 2. Basic Semantic Search (No Filters)
# ------------------------------------------------------------------
queries = [
    "Reset password",
    "How many days off do I get each year?",
]

for query in queries:
    results = collection.query(
        query_texts=[query],
        n_results=2
    )
    print_search_results(f"Query (Unfiltered): \"{query}\"", results)


# ------------------------------------------------------------------
# 3. Metadata Filtering (Enterprise Scope)
# ------------------------------------------------------------------
# Scenario: Suppose an employee asks "What is the policy?"
# Without a filter, general policies from any department match.
# With a filter, we restrict results strictly to IT or HR.

query = "What are the rules and guidelines?"

# Search only IT department
it_results = collection.query(
    query_texts=[query],
    n_results=2,
    where={"department": "IT"}
)
print_search_results(f"Query: \"{query}\" [Filter: department == 'IT']", it_results)

# Search only HR department
hr_results = collection.query(
    query_texts=[query],
    n_results=2,
    where={"department": "HR"}
)
print_search_results(f"Query: \"{query}\" [Filter: department == 'HR']", hr_results)

