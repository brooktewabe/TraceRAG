from typing import TypedDict, Literal, List, Optional
import os
from langgraph.graph import StateGraph, END

from src.config import settings
from src.retrieval.vector_search import VectorSearchEngine
from src.core.models import SearchResult, RAGQueryResponse


class AgentState(TypedDict):
    original_query: str
    current_query: str
    failed_queries: List[str]
    department: Optional[str]
    user_role: str
    documents: List[SearchResult]
    best_distance: float
    retry_count: int
    abstained: bool
    answer: str
    sources: List[str]
    trace: List[str]


search_engine = VectorSearchEngine()


def retrieve_node(state: AgentState) -> dict:
    query = state["current_query"]
    results = search_engine.search(
        query=query,
        department=state["department"],
        user_role=state["user_role"],
        top_k=settings.DEFAULT_TOP_K,
        threshold=1.0  # Fetch candidates to evaluate exact distance
    )

    best_dist = results[0].distance if results else 1.0
    trace_msg = f"Retrieved {len(results)} docs for '{query}' (Best Distance: {best_dist:.4f})"

    return {
        "documents": results,
        "best_distance": best_dist,
        "trace": state["trace"] + [trace_msg]
    }


def assess_node(state: AgentState) -> dict:
    dist = state["best_distance"]
    passed = dist <= settings.RELEVANCE_DISTANCE_THRESHOLD
    assessment = (
        f"Assessment: PASS ({dist:.4f} <= {settings.RELEVANCE_DISTANCE_THRESHOLD})"
        if passed
        else f"Assessment: FAIL ({dist:.4f} > {settings.RELEVANCE_DISTANCE_THRESHOLD})"
    )
    return {"trace": state["trace"] + [assessment]}


def rewrite_query_node(state: AgentState) -> dict:
    original = state["original_query"]
    last_query = state["current_query"]
    failed = state.get("failed_queries", []) + [last_query]
    retry = state["retry_count"] + 1

    rewritten = None
    ai_key = settings.GEMINI_API_KEY or settings.OPENAI_API_KEY
    if ai_key:
        try:
            if settings.GEMINI_API_KEY:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = (
                    f"You are an enterprise search optimizer.\n"
                    f"User question: '{original}'.\n"
                    f"The following searches failed to retrieve documents: {failed}.\n"
                    f"Generate a DIFFERENT 3-5 keyword search query for an enterprise knowledge base.\n"
                    f"Output ONLY the keywords."
                )
                resp = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )
                rewritten = resp.text.strip().replace('"', '')
        except Exception:
            pass

    if not rewritten:
        filler = {"how", "do", "i", "can", "what", "are", "the", "for", "a", "getting"}
        words = [w for w in original.lower().split() if w not in filler]
        variations = [
            "policy guidelines",
            "operating procedure",
            "workplace standard",
            "general compliance"
        ]
        suffix = variations[(retry - 1) % len(variations)]
        rewritten = " ".join(words) + f" {suffix}"

    trace_msg = f"Rewrote query to '{rewritten}' (Retry #{retry})"
    return {
        "current_query": rewritten,
        "failed_queries": failed,
        "retry_count": retry,
        "trace": state["trace"] + [trace_msg]
    }


def generate_answer_node(state: AgentState) -> dict:
    docs = state["documents"]
    sources = list(dict.fromkeys([f"{d.title} ({d.department})" for d in docs]))

    context_lines = []
    for i, d in enumerate(docs, 1):
        context_lines.append(f"[{i}] {d.title} ({d.department}): {d.content}")
    context_str = "\n".join(context_lines)

    answer = None
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = (
                f"You are a helpful company internal assistant. "
                f"Answer strictly using ONLY the provided context below.\n"
                f"Always include citations like [1] in your statements.\n\n"
                f"Context:\n{context_str}\n\n"
                f"Question: {state['original_query']}\n\n"
                f"Answer:"
            )
            resp = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            answer = resp.text.strip()
        except Exception:
            pass

    if not answer:
        top_doc = docs[0]
        answer = (
            f"Based on the {top_doc.title} [1], "
            f"{top_doc.content[:160]}..."
        )

    return {
        "answer": answer,
        "sources": sources,
        "abstained": False,
        "trace": state["trace"] + ["Generated grounded response with citations"]
    }


def abstain_node(state: AgentState) -> dict:
    msg = (
        "I could not locate sufficient documentation in the knowledge base "
        f"to reliably answer your question regarding '{state['original_query']}'. "
        "Please submit an IT or HR helpdesk inquiry for personalized assistance."
    )
    return {
        "answer": msg,
        "sources": [],
        "abstained": True,
        "trace": state["trace"] + ["Abstained: Retrieval score below safety threshold"]
    }


def route_after_assessment(state: AgentState) -> Literal["generate", "rewrite", "abstain"]:
    if state["best_distance"] <= settings.RELEVANCE_DISTANCE_THRESHOLD:
        return "generate"
    if state["retry_count"] < settings.MAX_RETRIES:
        return "rewrite"
    return "abstain"


def build_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("assess", assess_node)
    workflow.add_node("rewrite", rewrite_query_node)
    workflow.add_node("generate", generate_answer_node)
    workflow.add_node("abstain", abstain_node)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "assess")
    workflow.add_conditional_edges(
        "assess",
        route_after_assessment,
        {
            "generate": "generate",
            "rewrite": "rewrite",
            "abstain": "abstain"
        }
    )
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("generate", END)
    workflow.add_edge("abstain", END)

    return workflow.compile()


agent_app = build_agent_graph()


def ask_knowledge_agent(
    query: str,
    department: Optional[str] = None,
    user_role: str = "all_employees"
) -> RAGQueryResponse:
    initial_state: AgentState = {
        "original_query": query,
        "current_query": query,
        "failed_queries": [],
        "department": department,
        "user_role": user_role,
        "documents": [],
        "best_distance": 1.0,
        "retry_count": 0,
        "abstained": False,
        "answer": "",
        "sources": [],
        "trace": []
    }

    final_state = agent_app.invoke(initial_state)

    conf = max(0.0, min(1.0, 1.0 - final_state["best_distance"]))
    return RAGQueryResponse(
        query=query,
        answer=final_state["answer"],
        abstained=final_state["abstained"],
        confidence_score=round(conf, 4),
        sources=final_state["sources"],
        decision_trace=final_state["trace"]
    )

