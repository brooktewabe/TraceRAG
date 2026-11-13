"""
Phase 1 — Step 1: Embed documents and inspect the vectors.

Learning goals:
  1. Understand what model.encode() does.
  2. Inspect the shape of an embedding vector.
  3. See that two different phrasings of the same idea produce similar vectors.

Run:
    python step1_embed_and_inspect.py
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from documents import DOCUMENTS

# ------------------------------------------------------------------
# Load the embedding model
# ------------------------------------------------------------------
# 'all-MiniLM-L6-v2' is a small, fast model good for learning.
# It produces 384-dimensional vectors.
# The first run downloads the model (~80 MB) and caches it locally.
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded.\n")

# ------------------------------------------------------------------
# Embed all documents
# ------------------------------------------------------------------
# What goes in?  A list of strings (the document content).
# What happens?  Each string is tokenized and passed through the model.
# What comes out? A 2-D numpy array: shape (num_docs, 384).
texts = [doc["content"] for doc in DOCUMENTS]
doc_embeddings = model.encode(texts, show_progress_bar=True)

print(f"\nEmbedded {len(DOCUMENTS)} documents.")
print(f"Embedding shape: {doc_embeddings.shape}")
print(f"  → {doc_embeddings.shape[0]} documents")
print(f"  → {doc_embeddings.shape[1]} dimensions per vector")

# ------------------------------------------------------------------
# Inspect one vector
# ------------------------------------------------------------------
print("\n--- First 10 values of the 'Password Recovery' vector ---")
print(doc_embeddings[0, :10])
print("(These numbers have no individual meaning; their combination encodes the text's meaning.)")

# ------------------------------------------------------------------
# Compare two phrasings of the same idea
# ------------------------------------------------------------------
# These two phrases mean the same thing but use different words.
phrase_a = "Reset password"
phrase_b = "Password recovery"

vec_a = model.encode(phrase_a)
vec_b = model.encode(phrase_b)

# Cosine similarity: dot product of unit vectors.
# Range: -1 (opposite) to 1 (identical direction).
# Values above ~0.7 usually indicate strong semantic similarity.
def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

similarity = cosine_similarity(vec_a, vec_b)

print(f"\n--- Comparing two phrasings ---")
print(f"  Phrase A: '{phrase_a}'")
print(f"  Phrase B: '{phrase_b}'")
print(f"  Cosine similarity: {similarity:.4f}")
print("  Interpretation: values closer to 1.0 mean more similar meaning.")

# For contrast, compare something unrelated
phrase_c = "Annual leave balance"
vec_c = model.encode(phrase_c)
sim_a_c = cosine_similarity(vec_a, vec_c)
print(f"\n  Phrase A: '{phrase_a}'")
print(f"  Phrase C: '{phrase_c}'  (unrelated topic)")
print(f"  Cosine similarity: {sim_a_c:.4f}")
print("  → Should be lower than the A–B similarity above.\n")

