import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from src.retrieval.vector_search import VectorSearchEngine
from src.core.security import is_authorized
from src.ingestion.indexer import DocumentIndexer


@pytest.fixture(scope="module")
def search_engine():
    indexer = DocumentIndexer()
    indexer.run_full_sync()
    return VectorSearchEngine()


def test_password_recovery_semantic_retrieval(search_engine):
    results = search_engine.search("Reset password", top_k=1)
    assert len(results) > 0
    assert results[0].id == "doc_01"
    assert "Password Recovery" in results[0].title


def test_department_metadata_filtering(search_engine):
    it_results = search_engine.search("guidelines", department="IT", top_k=5)
    for r in it_results:
        assert r.department == "IT"


def test_rbac_security_isolation(search_engine):
    # doc_11 is restricted to 'manager'
    res_employee = search_engine.get_document_by_id("doc_11", user_role="all_employees")
    assert res_employee is None

    res_manager = search_engine.get_document_by_id("doc_11", user_role="manager")
    assert res_manager is not None
    assert res_manager.id == "doc_11"


def test_out_of_domain_abstention_threshold(search_engine):
    # Baking bread should not meet relevance threshold
    results = search_engine.search("How to bake sourdough bread?", top_k=3, threshold=0.55)
    assert len(results) == 0

