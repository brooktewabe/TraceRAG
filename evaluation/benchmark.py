"""
Evaluation & Benchmark Runner.

Runs the 20 ground-truth enterprise test queries against:
  1. Keyword Search Baseline (representing legacy keyword search)
  2. Vector Semantic Search (Sentence Transformers + Chroma)
  3. Agentic RAG Workflow (LangGraph)

Measures and compares:
  - Recall@1 & Recall@3
  - Mean Reciprocal Rank (MRR)
  - Out-of-Domain Abstention Accuracy
  - Average Query Latency (ms)

Run:
    python evaluation/benchmark.py
"""

import time
import sys
from pathlib import Path

# Ensure root workspace is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Dict, Any, List
from evaluation.test_dataset import BENCHMARK_QUERIES
from src.retrieval.vector_search import VectorSearchEngine
from src.retrieval.hybrid_search import KeywordSearchBaseline
from src.workflows.agent import ask_knowledge_agent
from src.ingestion.indexer import DocumentIndexer


def run_benchmark() -> Dict[str, Any]:
    print("=" * 80)
    print("ENTERPRISE AI KNOWLEDGE PLATFORM — EVALUATION BENCHMARK")
    print("=" * 80)

    # Ensure documents are synced
    indexer = DocumentIndexer()
    indexer.run_full_sync()

    keyword_engine = KeywordSearchBaseline()
    vector_engine = VectorSearchEngine()

    in_domain = [q for q in BENCHMARK_QUERIES if q["expected_doc_id"] is not None]
    out_domain = [q for q in BENCHMARK_QUERIES if q["expected_doc_id"] is None]

    print(f"Dataset summary: {len(in_domain)} In-Domain queries | {len(out_domain)} Out-of-Domain queries\n")

    # -------------------------------------------------------------
    # 1. Evaluate Keyword Baseline
    # -------------------------------------------------------------
    kw_hits_at_1 = 0
    kw_hits_at_3 = 0
    kw_reciprocal_ranks = []
    kw_latencies = []

    for item in in_domain:
        start = time.perf_counter()
        results = keyword_engine.search(item["query"], top_k=3)
        kw_latencies.append((time.perf_counter() - start) * 1000)

        retrieved_ids = [r.id for r in results]
        expected = item["expected_doc_id"]

        if retrieved_ids and retrieved_ids[0] == expected:
            kw_hits_at_1 += 1
            kw_reciprocal_ranks.append(1.0)
        elif expected in retrieved_ids:
            rank = retrieved_ids.index(expected) + 1
            kw_reciprocal_ranks.append(1.0 / rank)
        else:
            kw_reciprocal_ranks.append(0.0)

        if expected in retrieved_ids:
            kw_hits_at_3 += 1

    kw_recall_1 = (kw_hits_at_1 / len(in_domain)) * 100
    kw_recall_3 = (kw_hits_at_3 / len(in_domain)) * 100
    kw_mrr = sum(kw_reciprocal_ranks) / len(kw_reciprocal_ranks)
    kw_avg_lat = sum(kw_latencies) / len(kw_latencies)

    # -------------------------------------------------------------
    # 2. Evaluate Vector Semantic Search
    # -------------------------------------------------------------
    vec_hits_at_1 = 0
    vec_hits_at_3 = 0
    vec_reciprocal_ranks = []
    vec_latencies = []

    for item in in_domain:
        start = time.perf_counter()
        results = vector_engine.search(item["query"], top_k=3, threshold=1.0)
        vec_latencies.append((time.perf_counter() - start) * 1000)

        retrieved_ids = [r.id for r in results]
        expected = item["expected_doc_id"]

        if retrieved_ids and retrieved_ids[0] == expected:
            vec_hits_at_1 += 1
            vec_reciprocal_ranks.append(1.0)
        elif expected in retrieved_ids:
            rank = retrieved_ids.index(expected) + 1
            vec_reciprocal_ranks.append(1.0 / rank)
        else:
            vec_reciprocal_ranks.append(0.0)

        if expected in retrieved_ids:
            vec_hits_at_3 += 1

    vec_recall_1 = (vec_hits_at_1 / len(in_domain)) * 100
    vec_recall_3 = (vec_hits_at_3 / len(in_domain)) * 100
    vec_mrr = sum(vec_reciprocal_ranks) / len(vec_reciprocal_ranks)
    vec_avg_lat = sum(vec_latencies) / len(vec_latencies)

    # -------------------------------------------------------------
    # 3. Evaluate Out-of-Domain Guardrail (Abstention Rate)
    # -------------------------------------------------------------
    correct_abstentions = 0
    for item in out_domain:
        res = ask_knowledge_agent(item["query"])
        if res.abstained:
            correct_abstentions += 1

    abstention_rate = (correct_abstentions / len(out_domain)) * 100

    # -------------------------------------------------------------
    # Summary Report
    # -------------------------------------------------------------
    print("-" * 80)
    print(f"{'Metric':<35} | {'Keyword Search':<18} | {'Semantic Search':<18}")
    print("-" * 80)
    print(f"{'Recall @ 1 (Top Match Accuracy)':<35} | {kw_recall_1:>16.1f}% | {vec_recall_1:>16.1f}%")
    print(f"{'Recall @ 3 (Top 3 Candidates)':<35} | {kw_recall_3:>16.1f}% | {vec_recall_3:>16.1f}%")
    print(f"{'Mean Reciprocal Rank (MRR)':<35} | {kw_mrr:>18.3f} | {vec_mrr:>18.3f}")
    print(f"{'Average Latency':<35} | {kw_avg_lat:>14.2f} ms | {vec_avg_lat:>14.2f} ms")
    print("-" * 80)
    print(f"Out-of-Domain Abstention Accuracy (Agentic Guardrail): {abstention_rate:.1f}%\n")

    return {
        "keyword_recall_3": kw_recall_3,
        "semantic_recall_3": vec_recall_3,
        "semantic_mrr": vec_mrr,
        "abstention_rate": abstention_rate
    }


if __name__ == "__main__":
    run_benchmark()
