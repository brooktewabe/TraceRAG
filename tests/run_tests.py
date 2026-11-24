import sys
from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.retrieval.vector_search import VectorSearchEngine
from src.ingestion.indexer import DocumentIndexer
from src.workflows.agent import ask_knowledge_agent


class TestEnterpriseKnowledgePlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        indexer = DocumentIndexer()
        indexer.run_full_sync()
        cls.search_engine = VectorSearchEngine()

    def test_semantic_retrieval(self):
        """Verify semantic matching without keyword overlap ('Reset password' -> Password Recovery)."""
        results = self.search_engine.search("Reset password", top_k=1)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].id, "doc_01")

    def test_metadata_scoping(self):
        """Verify queries restricted to IT only return IT documents."""
        results = self.search_engine.search("policy", department="IT", top_k=3)
        for r in results:
            self.assertEqual(r.department, "IT")

    def test_rbac_security_boundaries(self):
        """Verify employees cannot access executive/manager compensation docs."""
        doc_employee = self.search_engine.get_document_by_id("doc_11", user_role="all_employees")
        self.assertIsNone(doc_employee)

        doc_manager = self.search_engine.get_document_by_id("doc_11", user_role="manager")
        self.assertIsNotNone(doc_manager)
        self.assertEqual(doc_manager.id, "doc_11")

    def test_agentic_rag_abstention(self):
        """Verify out-of-domain queries trigger safety abstention."""
        response = ask_knowledge_agent("How to bake sourdough bread?")
        self.assertTrue(response.abstained)
        self.assertIn("could not locate sufficient documentation", response.answer)


if __name__ == "__main__":
    unittest.main()

