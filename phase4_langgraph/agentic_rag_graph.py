"""
Phase 4 — Agentic RAG with LangGraph.

Why LangGraph?
In Phase 3, the RAG pipeline was strictly LINEAR:
    Query -> Retrieve -> Prompt -> Answer
If the query was ambiguous or the search missed the target, linear RAG fails immediately.

In Phase 4, we introduce a STATE GRAPH that can make decisions and loop:
    1. Retrieve documents from Chroma.
    2. Assess: Is the evidence relevant enough?
    3. Branch:
       - If YES: Generate answer -> END.
       - If NO & retry_count == 0: Rewrite the query -> Loop back to Retrieve!
       - If NO & retry_count >= 1: Abstain gracefully -> END.

The Learning Rule:
  1. What goes in?
     - `AgentState` containing the initial user query.
  2. What happens internally?
     - Nodes update state variables (`query`, `documents`, `relevance_score`, `retry_count`, `answer`).
     - Conditional edges evaluate state and route execution dynamically.
  3. What comes out?
     - Final updated state containing the grounded answer (or safe abstention) and the complete decision trace.

Run:
    python agentic_rag_graph.py
"""

from typing import TypedDict, Literal
from pathlib import Path
import os
from dotenv import load_dotenv

import chromadb
from chromadb.utils import embedding_functions
from langgraph.graph import StateGraph, END

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ------------------------------------------------------------------
# 1. Connect to Chroma Vector Store (From Phase 2)
# ------------------------------------------------------------------
DB_DIR = Path(__file__).resolve().parent.parent / "chroma_data"
client = chromadb.PersistentClient(path=str(DB_DIR))
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.get_collection(
    name="company_knowledge_base",
    embedding_function=embedding_fn
)


# ------------------------------------------------------------------
# 2. Define the Graph State
# ------------------------------------------------------------------
class AgentState(TypedDict):
    original_query: str      # The user's original query
    current_query: str       # The query currently used for retrieval (may be rewritten)
    documents: list[dict]    # Retrieved document chunks
    best_distance: float     # Cosine distance of the closest match (lower is closer)
    retry_count: int         # How many times we attempted a rewrite
    answer: str              # Generated answer or abstention message
    trace: list[str]         # Execution audit trail


# Thresholds for decision routing (cosine distance where 0.0 = identical)
GOOD_MATCH_THRESHOLD = 0.55     # Distance <= 0.55: high confidence match
MAX_RETRIES = 1                 # Allow 1 query rewrite attempt


# ------------------------------------------------------------------
# 3. Define Graph Nodes
# ------------------------------------------------------------------
def retrieve_node(state: AgentState) -> dict:
    """Node: Query Chroma using current_query."""
    query = state["current_query"]
    results = collection.query(query_texts=[query], n_results=2)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    retrieved = []
    best_dist = 1.0
    if docs:
        best_dist = dists[0]
        for doc, meta, dist in zip(docs, metas, dists):
            retrieved.append({
                "title": meta.get("title", "Unknown"),
                "department": meta.get("department", "General"),
                "content": doc,
                "distance": dist
            })

    trace_msg = f"Retrieved {len(retrieved)} docs for '{query}' (Best Distance: {best_dist:.4f})"
    return {
        "documents": retrieved,
        "best_distance": best_dist,
        "trace": state["trace"] + [trace_msg]
    }


def assess_node(state: AgentState) -> dict:
    """Node: Assess whether retrieved evidence is sufficient."""
    dist = state["best_distance"]
    if dist <= GOOD_MATCH_THRESHOLD:
        assessment = f"Assessment: PASS (Distance {dist:.4f} <= {GOOD_MATCH_THRESHOLD})"
    else:
        assessment = f"Assessment: FAIL (Distance {dist:.4f} > {GOOD_MATCH_THRESHOLD})"

    return {
        "trace": state["trace"] + [assessment]
    }


def rewrite_query_node(state: AgentState) -> dict:
    """Node: Rewrite query using an LLM or keyword expansion heuristics."""
    original = state["original_query"]
    retry = state["retry_count"] + 1

    # Attempt query rewriting via Gemini/OpenAI if available, else clean heuristic
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    rewritten = None

    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-3.5-flash")
            prompt = (
                f"You are an internal corporate search assistant. "
                f"The user searched: '{original}', but retrieval had low confidence. "
                f"Rewrite this query into 3-5 standard corporate policy keywords. "
                f"Output ONLY the rewritten query, nothing else."
            )
            response = model.generate_content(prompt)
            rewritten = response.text.strip().replace('"', '')
        except Exception as e:
            ai_error_note = f"(AI call failed: {e})"

    if not rewritten:
        # Fallback heuristic rewrite (removes conversational filler)
        filler_words = {"how", "do", "i", "can", "what", "are", "the", "for", "a", "getting"}
        words = [w for w in original.lower().split() if w not in filler_words]
        rewritten = " ".join(words) + " policy guidelines"

    trace_msg = f"Rewrote query from '{original}' to '{rewritten}' (Retry #{retry})"
    return {
        "current_query": rewritten,
        "retry_count": retry,
        "trace": state["trace"] + [trace_msg]
    }


def generate_answer_node(state: AgentState) -> dict:
    """Node: Generate grounded response with citations."""
    docs = state["documents"]
    context_lines = []
    for i, d in enumerate(docs, 1):
        context_lines.append(f"[{i}] {d['title']} ({d['department']}): {d['content']}")
    context_str = "\n".join(context_lines)

    prompt = (
        f"You are a company assistant. Answer based ONLY on the context below.\n"
        f"Include citations like [1] in your response.\n\n"
        f"Context:\n{context_str}\n\n"
        f"Question: {state['original_query']}\n\n"
        f"Answer:"
    )

    answer = None
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-3.5-flash")
            resp = model.generate_content(prompt)
            answer = resp.text.strip()
        except Exception as e:
            answer = f"(LLM error: {e})"

    if not answer:
        # Inspection response if no key is configured
        top_doc = docs[0]
        answer = (
            f"[Grounded Answer from {top_doc['title']}]:\n"
            f"{top_doc['content'][:150]}... (Distance: {top_doc['distance']:.4f})"
        )

    return {
        "answer": answer,
        "trace": state["trace"] + ["Generated final grounded answer with citations"]
    }


def abstain_node(state: AgentState) -> dict:
    """Node: Safely abstain when evidence is insufficient even after rewrites."""
    abstain_msg = (
        "I could not find sufficient documentation in the company knowledge base "
        f"to answer: '{state['original_query']}'. "
        "Please contact IT or HR directly if you need further assistance."
    )
    return {
        "answer": abstain_msg,
        "trace": state["trace"] + ["Abstained: Insufficient evidence in knowledge base"]
    }


# ------------------------------------------------------------------
# 4. Define Conditional Routing Function
# ------------------------------------------------------------------
def route_after_assessment(state: AgentState) -> Literal["generate", "rewrite", "abstain"]:
    """Conditional Edge: Decides whether to generate, rewrite, or abstain."""
    dist = state["best_distance"]

    if dist <= GOOD_MATCH_THRESHOLD:
        return "generate"

    if state["retry_count"] < MAX_RETRIES:
        return "rewrite"

    return "abstain"


# ------------------------------------------------------------------
# 5. Build and Compile the LangGraph Workflow
# ------------------------------------------------------------------
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("assess", assess_node)
workflow.add_node("rewrite", rewrite_query_node)
workflow.add_node("generate", generate_answer_node)
workflow.add_node("abstain", abstain_node)

# Add Edges
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "assess")

# Conditional Edge from 'assess'
workflow.add_conditional_edges(
    "assess",
    route_after_assessment,
    {
        "generate": "generate",
        "rewrite": "rewrite",
        "abstain": "abstain"
    }
)

# Loop edge: after rewriting query, loop back to retrieve!
workflow.add_edge("rewrite", "retrieve")

# End edges
workflow.add_edge("generate", END)
workflow.add_edge("abstain", END)

# Compile into an executable graph application
app = workflow.compile()


# ------------------------------------------------------------------
# 6. Run Test Queries
# ------------------------------------------------------------------
def run_agentic_test(query: str):
    print("=" * 75)
    print(f"TEST QUERY: \"{query}\"")
    print("=" * 75)

    initial_state: AgentState = {
        "original_query": query,
        "current_query": query,
        "documents": [],
        "best_distance": 1.0,
        "retry_count": 0,
        "answer": "",
        "trace": []
    }

    final_state = app.invoke(initial_state)

    print("DECISION TRACE (Workflow Path):")
    for step in final_state["trace"]:
        print(f"  → {step}")

    print("\nFINAL ANSWER:")
    print(final_state["answer"])
    print()


if __name__ == "__main__":
    # Test 1: Direct Match -> Should take: retrieve -> assess -> generate -> END
    run_agentic_test("How do I reset my forgotten password?")

    # Test 2: Conversational / Indirect -> Should take: retrieve -> assess -> REWRITE -> retrieve -> assess -> generate -> END
    run_agentic_test("getting money back for buying lunch on business trips")

    # Test 3: Out-of-Domain -> Should take: retrieve -> assess -> REWRITE -> retrieve -> assess -> ABSTAIN -> END
    run_agentic_test("How do I bake sourdough bread?")

