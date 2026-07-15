# ingest.py
"""
Populates the Qdrant collection from the .txt files in data/policies/.

Can be run standalone:  python ingest.py
...or imported and called as run_ingestion() -- retriever.py does this
automatically the first time it's used if the collection is missing
or empty. That matters on environments like Streamlit Cloud, which
use an ephemeral filesystem: a local Qdrant path (vectordb/) built on
your machine won't be there after a fresh deploy, but data/policies/
*is* committed to the repo, so the app can self-heal on first use
instead of crashing.
"""

from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http import models

from llm import embeddings, qdrant_client

# ----------------------------------------
# Configuration
# ----------------------------------------

COLLECTION_NAME = "insurance_policies"

# FIX: resolved relative to this file, not the process's current
# working directory -- Streamlit Cloud / different launch methods
# don't always run from the project root.
DATA_FOLDER = Path(__file__).resolve().parent / "data" / "policies"


def run_ingestion(data_folder: Path = DATA_FOLDER, verbose: bool = True) -> int:
    """
    Loads *.txt files from data_folder, chunks them, and (re)populates
    the Qdrant collection. Returns the number of chunks stored.
    """

    documents = []
    for file in sorted(data_folder.glob("*.txt")):
        text = file.read_text(encoding="utf-8")
        documents.append(
            Document(page_content=text, metadata={"source": file.name})
        )

    if verbose:
        print(f"Loaded {len(documents)} documents from {data_folder}")

    if not documents:
        if verbose:
            print(f"No .txt files found in {data_folder} -- nothing to ingest.")
        return 0

    # ----------------------------------------
    # Split into chunks
    # ----------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120
    )

    chunks = splitter.split_documents(documents)
    if verbose:
        print(f"Created {len(chunks)} chunks")

    # ----------------------------------------
    # Create collection if it doesn't exist
    # ----------------------------------------

    collections = qdrant_client.get_collections().collections
    collection_names = [c.name for c in collections]

    if COLLECTION_NAME not in collection_names:
        if verbose:
            print(f"Creating collection: {COLLECTION_NAME}...")

        vector_size = len(embeddings.embed_query("test"))

        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        if verbose:
            print(f"Collection '{COLLECTION_NAME}' created with vector size {vector_size}.")
    else:
        if verbose:
            print(f"Collection '{COLLECTION_NAME}' already exists.")

    # ----------------------------------------
    # Add documents
    # ----------------------------------------

    vectorstore = QdrantVectorStore(
        client=qdrant_client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings
    )

    if verbose:
        print("Adding documents to Qdrant...")
    vectorstore.add_documents(chunks)

    if verbose:
        print("✅ Qdrant collection created and populated successfully!")
        print(f"Stored {len(chunks)} chunks.")

    return len(chunks)


if __name__ == "__main__":
    run_ingestion()
