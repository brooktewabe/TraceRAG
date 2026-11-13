"""
Phase 1 — Step 2: Semantic search (raw cosine similarity, no frameworks).

Learning goals:
  1. Embed a query.
  2. Compare it against all document vectors.
  3. Rank documents by similarity score.
  4. Understand why "Reset password" retrieves "Password Recovery."

Run:
    python step2_semantic_search.py
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from documents import DOCUMENTS

# ------------------------------------------------------------------
# Load model and embed all documents
# ------------------------------------------------------------------
print("Loading model and embedding documents...")
model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [doc["content"] for doc in DOCUMENTS]
doc_embeddings = model.encode(texts)
print("Ready.\n")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors."""
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def semantic_search(query: str, top_k: int = 3) -> list[dict]:
    """
    What goes in?   A query string.
    What happens?   The query is embedded; its vector is compared to every
                    document vector using cosine similarity.
    What comes out? A ranked list of the top-k results with scores.
    """
    query_vec = model.encode(query)

    scores = [
        {
            "rank": 0,          # filled in after sorting
            "score": cosine_similarity(query_vec, doc_embeddings[i]),
            "title": DOCUMENTS[i]["title"],
            "id": DOCUMENTS[i]["id"],
            "snippet": DOCUMENTS[i]["content"][:120] + "...",
        }
        for i in range(len(DOCUMENTS))
    ]

    # Sort descending by score
    scores.sort(key=lambda x: x["score"], reverse=True)

    for rank, result in enumerate(scores[:top_k], start=1):
        result["rank"] = rank

    return scores[:top_k]


def print_results(query: str, results: list[dict]) -> None:
    print(f'Query: "{query}"')
    print("-" * 60)
    for r in results:
        print(f"  #{r['rank']}  [{r['score']:.4f}]  {r['title']}  ({r['id']})")
        print(f"       {r['snippet']}")
    print()


# ------------------------------------------------------------------
# Run the test queries from your notes
# ------------------------------------------------------------------
test_queries = [
    "Reset password",
    "Work from home",
    "How many vacation days do employees receive?",
    "Badge and building access",           # not a phrase from any document
    "What happens if I harass a colleague?",
    "What does vector embedding mean?"
]

for query in test_queries:
    results = semantic_search(query, top_k=3)
    print_results(query, results)

