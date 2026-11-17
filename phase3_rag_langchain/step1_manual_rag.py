"""
Phase 3 — Step 1: Manual RAG (No LangChain yet!).

Before using abstractions like LangChain, we build RAG from first principles.

The Learning Rule:
  1. What goes in?
     - A user question (string).
  2. What happens internally?
     - Query Chroma for the top K closest chunks and their distances.
     - Relevance threshold check: if closest document distance > 0.60, ABSTAIN.
     - Extract clean context and metadata.
     - Construct a grounded prompt with explicit citation instructions.
     - Invoke the LLM (or fallback inspector if no API key is provided).
  3. What comes out?
     - Grounded answer string with source citations.

Run:
    python step1_manual_rag.py
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

# Load environment variables from .env
load_dotenv()

# ------------------------------------------------------------------
# 1. Connect to Chroma DB from Phase 2
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
# 2. Configurable Relevance Threshold
# ------------------------------------------------------------------
# In cosine space: distance = 1 - cosine_similarity.
# Distance 0.0 = identical.
# Distance > 0.60 means similarity is < 0.40 (not relevant enough to answer safely).
RELEVANCE_DISTANCE_THRESHOLD = 0.60


def retrieve_context(query: str, top_k: int = 3) -> tuple[list[dict], bool]:
    """
    Retrieve documents and check if evidence meets the relevance threshold.
    Returns: (list_of_chunks, is_sufficient)
    """
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    if not docs or dists[0] > RELEVANCE_DISTANCE_THRESHOLD:
        # Best match is too far; insufficient evidence to answer reliably
        return [], False

    chunks = []
    for doc, meta, dist in zip(docs, metas, dists):
        # Only include chunks that meet our threshold
        if dist <= RELEVANCE_DISTANCE_THRESHOLD:
            chunks.append({
                "content": doc,
                "title": meta.get("title", "Unknown"),
                "department": meta.get("department", "General"),
                "distance": dist
            })

    return chunks, len(chunks) > 0


def build_rag_prompt(query: str, chunks: list[dict]) -> str:
    """
    Format evidence and assemble strict system instructions to prevent hallucination.
    """
    context_blocks = []
    for idx, c in enumerate(chunks, start=1):
        context_blocks.append(
            f"[{idx}] Document: {c['title']} (Department: {c['department']})\n"
            f"Content: {c['content']}"
        )
    formatted_context = "\n\n".join(context_blocks)

    prompt = f"""You are a helpful company internal assistant.
Answer the user's question STRICTLY using only the provided context below.
If the answer cannot be found in the context, say "I don't have enough information in company documents to answer this."
Always cite the source number (e.g. [1]) when making statements.

CONTEXT:
{formatted_context}

USER QUESTION:
{query}

ANSWER:"""
    return prompt


def call_llm(prompt: str) -> str:
    """
    Calls Gemini (or OpenAI if present). If no API key is found,
    shows an inspection preview.
    """
    # 1. Check for Gemini API key
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-3.8-flash")
            response = model.generate_content(prompt)
            return response.text
        except ImportError:
            return (
                "[Missing dependency] 'google-generativeai' is not installed yet.\n"
                "Run: pip install google-generativeai"
            )
        except Exception as e:
            return f"(Gemini API call error: {e})"

    # 2. Check for OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"(OpenAI API call error: {e})"

    # 3. Fallback inspection mode
    return (
        "[Inspection Mode - No API Key Set]\n"
        "Set GEMINI_API_KEY in your .env file to get live responses."
    )


def ask_rag(query: str) -> None:
    print("=" * 70)
    print(f"User Query: \"{query}\"")
    print("=" * 70)

    # 1. Retrieve
    chunks, is_sufficient = retrieve_context(query)

    # 2. Check Abstention condition
    if not is_sufficient:
        print("Status: [ABSTAINED]")
        print("Reason: No documents in the database met the relevance threshold (distance > 0.60).")
        print("Response: I am sorry, but I do not have enough documentation to answer this question.\n")
        return

    print(f"Status: [RETRIEVED {len(chunks)} RELEVANT CHUNKS]")
    for i, c in enumerate(chunks, 1):
        print(f"  [{i}] {c['title']} ({c['department']}) | Distance: {c['distance']:.4f}")
    print()

    # 3. Build Prompt
    prompt = build_rag_prompt(query, chunks)
    print("--- Generated Prompt (Grounding Context) ---")
    print(prompt)
    print("-" * 70)

    # 4. Generate Answer
    answer = call_llm(prompt)
    print("--- Final Answer ---")
    print(answer)
    print()


# ------------------------------------------------------------------
# Test Scenarios
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Scenario A: Highly relevant question (should retrieve & answer)
    ask_rag("How can I reset my forgotten password?")

    # Scenario B: Partial phrasing match (should retrieve remote work policy)
    ask_rag("Can I work from home and do I need a VPN?")

    # Scenario C: Out-of-domain query (should ABSTAIN!)
    ask_rag("What is the recipe for chocolate chip cookies?")

