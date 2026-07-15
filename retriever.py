"""
Retrieve relevant policy documents from Qdrant.
"""

from langchain_qdrant import QdrantVectorStore

from llm import embeddings, qdrant_client

# ------------------------------------------
# Configuration
# ------------------------------------------

COLLECTION_NAME = "insurance_policies"

_retriever = None


def get_collection_status():
    """
    Returns (ready, points_count) -- ready is True if the collection
    exists and has at least one chunk stored. Used by app.py to show
    a status indicator, and internally to decide whether to
    auto-ingest.
    """
    try:
        info = qdrant_client.get_collection(COLLECTION_NAME)
        count = info.points_count or 0
        return count > 0, count
    except Exception:
        return False, 0


def _get_retriever():
    global _retriever

    if _retriever is None:
        # FIX: previously `vectorstore = QdrantVectorStore(...)` ran
        # at module import time. langchain_qdrant validates that the
        # collection already exists as part of __init__, so on any
        # environment where ingest.py hasn't run yet -- e.g. a fresh
        # Streamlit Cloud deploy, whose filesystem is ephemeral and
        # won't have your local vectordb/ folder -- this raised
        # ValueError("Collection insurance_policies not found") and
        # crashed the app before it could render anything.
        #
        # Now we build the retriever lazily on first real use, and if
        # the collection is missing or empty we auto-run ingestion
        # from the .txt files in data/policies/ (which *are*
        # committed to the repo), so the app self-heals instead of
        # crashing.
        ready, _ = get_collection_status()
        if not ready:
            from ingest import run_ingestion
            run_ingestion()

        vectorstore = QdrantVectorStore(
            client=qdrant_client,
            collection_name=COLLECTION_NAME,
            embedding=embeddings
        )

        _retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 4
            }
        )

    return _retriever


def retrieve_documents(query: str):
    """
    Retrieve the most relevant policy chunks.
    """

    docs = _get_retriever().invoke(query)

    return docs

def format_documents(docs):
    """
    Convert LangChain Documents into a simpler structure.
    """

    formatted = []

    for doc in docs:

        formatted.append(
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown")
            }
        )

    return formatted
