"""
Phase 3 — Step 2: RAG with LangChain.

Now that you've seen manual RAG from first principles, this script shows
how LangChain packages those exact same steps into modular components:
  1. VectorStore Retriever (`as_retriever()`)
  2. PromptTemplate (`ChatPromptTemplate`)
  3. LCEL Chain (`retriever | format_docs | prompt | model | parser`)

Run:
    python step2_langchain_rag.py
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# LangChain components
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# ------------------------------------------------------------------
# 1. Connect Chroma as a LangChain VectorStore
# ------------------------------------------------------------------
DB_DIR = Path(__file__).resolve().parent.parent / "chroma_data"

# LangChain uses standard HuggingFaceEmbeddings wrapper
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = Chroma(
    collection_name="company_knowledge_base",
    embedding_function=embeddings,
    persist_directory=str(DB_DIR),
)

# Convert vectorstore into a Retriever
# This abstracts away the collection.query(...) loop
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 2}
)
# retriever = vectorstore.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={
#         "score_threshold": 0.6,  # Minimum relevance score (0 to 1)
#         "k": 4                    # Optional: max documents to return
#     }
# )
# ------------------------------------------------------------------
# 2. Define Prompt Template
# ------------------------------------------------------------------
template = """Answer the question based strictly on the following context:
{context}

Question: {question}

Answer with citations (e.g., [Doc Title]):"""

prompt = ChatPromptTemplate.from_template(template)


# ------------------------------------------------------------------
# 3. Helper to format retrieved documents
# ------------------------------------------------------------------
def format_docs(docs):
    formatted = []
    for d in docs:
        title = d.metadata.get("title", "Unknown")
        dept = d.metadata.get("department", "General")
        formatted.append(f"[{title} - {dept}]\n{d.page_content}")
    return "\n\n".join(formatted)


# ------------------------------------------------------------------
# 4. Construct the LCEL Pipeline
# ------------------------------------------------------------------
# How LCEL works:
# {"context": retriever | format_docs, "question": RunnablePassthrough()}
#   -> queries Chroma, formats docs into context string
#   -> pipes into prompt template
#   -> pipes into LLM
#   -> pipes into OutputParser

print("=" * 70)
print("LangChain RAG Pipeline Initialized")
print("=" * 70)

test_query = "What is the procedure for resetting a forgotten password?"
print(f"Testing retrieval for: \"{test_query}\"\n")

# Let's inspect the retriever output:
retrieved_docs = retriever.invoke(test_query)
for i, doc in enumerate(retrieved_docs, start=1):
    print(f"Retrieved Doc #{i}:")
    print(f"  Title: {doc.metadata.get('title')}")
    print(f"  Content: {doc.page_content[:100]}...\n")

# Check if an LLM is available (Gemini / OpenAI)
gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
openai_key = os.environ.get("OPENAI_API_KEY")

llm = None
if gemini_key:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            temperature=0.0,
            google_api_key=gemini_key
        )
        print("Using LLM: Google Gemini (gemini-3.8-flash)")
    except ImportError:
        print("[Notice] Run 'pip install langchain-google-genai' to enable live Gemini in LangChain.")
elif openai_key:
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        print("Using LLM: OpenAI (gpt-4o-mini)")
    except ImportError:
        print("[Notice] Run 'pip install langchain-openai' to enable live OpenAI in LangChain.")

if llm:
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    answer = rag_chain.invoke(test_query)
    print("\n--- LangChain Chain Output ---")
    print(answer)
else:
    print("\n--- LangChain Prompt Preview (No LLM initialized) ---")
    formatted_context = format_docs(retrieved_docs)
    rendered_prompt = prompt.format(context=formatted_context, question=test_query)
    print(rendered_prompt)

