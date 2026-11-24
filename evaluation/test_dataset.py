"""
Evaluation Benchmark Dataset.

Contains 20 representative enterprise search queries with ground truth annotations.
Includes:
  - In-domain semantic queries (varying from exact matches to conversational phrasing).
  - Out-of-domain queries (which must trigger ABSTENTION to prevent hallucinations).
"""

from typing import List, Dict, Any, Optional

BENCHMARK_QUERIES: List[Dict[str, Any]] = [
    # --- In-Domain IT Queries ---
    {
        "id": "q01",
        "query": "Reset password",
        "expected_doc_id": "doc_01",
        "department": "IT",
        "type": "synonym"
    },
    {
        "id": "q02",
        "query": "How do I unlock my account or reset multi factor authentication?",
        "expected_doc_id": "doc_01",
        "department": "IT",
        "type": "conversational"
    },
    {
        "id": "q03",
        "query": "Requesting a MacBook Pro or 4K monitors",
        "expected_doc_id": "doc_06",
        "department": "IT",
        "type": "semantic"
    },
    {
        "id": "q04",
        "query": "Hardware return policy when leaving the company",
        "expected_doc_id": "doc_06",
        "department": "IT",
        "type": "semantic"
    },

    # --- In-Domain HR Queries ---
    {
        "id": "q05",
        "query": "Work from home rules and VPN requirements",
        "expected_doc_id": "doc_02",
        "department": "HR",
        "type": "synonym"
    },
    {
        "id": "q06",
        "query": "Core working hours for remote workers",
        "expected_doc_id": "doc_02",
        "department": "HR",
        "type": "semantic"
    },
    {
        "id": "q07",
        "query": "How many vacation days do full-time employees receive?",
        "expected_doc_id": "doc_03",
        "department": "HR",
        "type": "direct"
    },
    {
        "id": "q08",
        "query": "Carrying over unused PTO into the next year",
        "expected_doc_id": "doc_03",
        "department": "HR",
        "type": "synonym"
    },
    {
        "id": "q09",
        "query": "What happens on the first day for new hires?",
        "expected_doc_id": "doc_07",
        "department": "HR",
        "type": "conversational"
    },
    {
        "id": "q10",
        "query": "How does the annual performance review rating scale work?",
        "expected_doc_id": "doc_10",
        "department": "HR",
        "type": "semantic"
    },

    # --- In-Domain Finance & Operations Queries ---
    {
        "id": "q11",
        "query": "Daily meal reimbursement limits on business travel",
        "expected_doc_id": "doc_05",
        "department": "Finance",
        "type": "semantic"
    },
    {
        "id": "q12",
        "query": "Receipt requirements and deadline for expense claims",
        "expected_doc_id": "doc_05",
        "department": "Finance",
        "type": "semantic"
    },
    {
        "id": "q13",
        "query": "Reporting a lost security badge or visitor escort rules",
        "expected_doc_id": "doc_04",
        "department": "Operations",
        "type": "semantic"
    },
    {
        "id": "q14",
        "query": "Severity 1 critical production outage escalation protocol",
        "expected_doc_id": "doc_12",
        "department": "Engineering",
        "type": "direct"
    },

    # --- In-Domain Legal & Compliance Queries ---
    {
        "id": "q15",
        "query": "Reporting discrimination or workplace harassment anonymously",
        "expected_doc_id": "doc_08",
        "department": "Legal",
        "type": "semantic"
    },
    {
        "id": "q16",
        "query": "Customer PII handling and reporting data breaches",
        "expected_doc_id": "doc_09",
        "department": "Legal",
        "type": "semantic"
    },

    # --- Out-of-Domain Queries (Expected to ABSTAIN / Zero match) ---
    {
        "id": "q17",
        "query": "How do I bake chocolate chip cookies at home?",
        "expected_doc_id": None,
        "department": None,
        "type": "out_of_domain"
    },
    {
        "id": "q18",
        "query": "What is the weather forecast for Tokyo tomorrow?",
        "expected_doc_id": None,
        "department": None,
        "type": "out_of_domain"
    },
    {
        "id": "q19",
        "query": "Who won the FIFA World Cup in 2022?",
        "expected_doc_id": None,
        "department": None,
        "type": "out_of_domain"
    },
    {
        "id": "q20",
        "query": "Best strategy for playing chess openings",
        "expected_doc_id": None,
        "department": None,
        "type": "out_of_domain"
    },
]

