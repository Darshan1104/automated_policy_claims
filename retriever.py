"""
Retrieve relevant policy documents from Qdrant.
"""

from langchain_qdrant import QdrantVectorStore

from llm import embeddings, qdrant_client

# ------------------------------------------
# Configuration
# ------------------------------------------

COLLECTION_NAME = "insurance_policies"

# ------------------------------------------
# Connect to Existing Collection
# ------------------------------------------

vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embedding=embeddings
)

# ------------------------------------------
# Retriever
# ------------------------------------------

# FIX: k=2 was thin, especially combined with the small chunk_size
# in ingest.py -- easy to miss relevant clauses. Bumped to 4.
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 4
    }
)


def retrieve_documents(query: str):
    """
    Retrieve the most relevant policy chunks.
    """

    docs = retriever.invoke(query)

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