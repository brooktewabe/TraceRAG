import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastmcp import FastMCP
from src.retrieval.vector_search import VectorSearchEngine

mcp = FastMCP("EnterpriseKnowledgePlatform")
search_engine = VectorSearchEngine()


@mcp.tool()
def search_knowledge_base(
    query: str,
    department: str = "",
    user_role: str = "all_employees",
    top_k: int = 3
) -> str:
    """
    Search enterprise company policies and technical documentation using semantic retrieval.

    Args:
        query: Search keywords or question (e.g. 'how to reset password', 'remote work rules').
        department: Optional department filter (e.g. 'IT', 'HR', 'Finance', 'Legal', 'Operations').
        user_role: Caller role for RBAC permissions ('all_employees', 'manager', 'admin').
        top_k: Maximum number of relevant documents to retrieve.
    """
    results = search_engine.search(
        query=query,
        department=department if department else None,
        user_role=user_role,
        top_k=top_k
    )

    if not results:
        return f"No documentation found matching '{query}' within authorized permissions."

    formatted = []
    for r in results:
        formatted.append(
            f"• Title: {r.title} [{r.department}]\n"
            f"  Relevance: {r.relevance_score:.2f} (Distance: {r.distance:.4f})\n"
            f"  Content: {r.content}"
        )
    return "\n\n".join(formatted)


@mcp.tool()
def get_document(doc_id: str, user_role: str = "all_employees") -> str:
    """
    Retrieve full details for a specific enterprise document ID with permission enforcement.

    Args:
        doc_id: Document ID string (e.g. 'doc_01', 'doc_02').
        user_role: Caller role for permission checks.
    """
    doc = search_engine.get_document_by_id(doc_id, user_role)
    if not doc:
        return f"Document '{doc_id}' not found or access denied."

    return (
        f"ID: {doc.id}\n"
        f"Title: {doc.title}\n"
        f"Department: {doc.department}\n"
        f"Category: {doc.category}\n"
        f"Access Level: {doc.access_level}\n\n"
        f"Content:\n{doc.content}"
    )


@mcp.tool()
def list_departments() -> str:
    """
    List all available company departments indexed in the knowledge platform.
    """
    depts = search_engine.list_departments()
    return "Available Departments:\n" + "\n".join(f"- {d}" for d in depts)


if __name__ == "__main__":
    mcp.run()
