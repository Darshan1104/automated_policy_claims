# ingest.py
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from llm import embeddings, qdrant_client
from qdrant_client.http import models

# ----------------------------------------
# Configuration
# ----------------------------------------

COLLECTION_NAME = "insurance_policies"
DATA_FOLDER = Path("data/policies")

# ----------------------------------------
# Load text files
# ----------------------------------------

documents = []

for file in DATA_FOLDER.glob("*.txt"):
    text = file.read_text(encoding="utf-8")
    documents.append(
        Document(
            page_content=text,
            metadata={"source": file.name}
        )
    )

print(f"Loaded {len(documents)} documents")

# ----------------------------------------
# Split into chunks
# ----------------------------------------

# FIX: chunk_size=180 / chunk_overlap=20 was far too small for policy
# text -- clauses get sliced mid-sentence, which starves the
# retrieval grader and decision node of coherent context (a likely
# contributor to claims bouncing to MANUAL_REVIEW or getting graded
# "not relevant" incorrectly). Bumped to sizes that keep whole
# clauses together.
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120
)

chunks = splitter.split_documents(documents)
print(f"Created {len(chunks)} chunks")

# ----------------------------------------
# Create Collection Manually (Bypassing the bug)
# ----------------------------------------

# Check if collection exists
collections = qdrant_client.get_collections().collections
collection_names = [c.name for c in collections]

if COLLECTION_NAME not in collection_names:
    print(f"Creating collection: {COLLECTION_NAME}...")

    # Get embedding dimension (usually 384 for bge-small-en-v1.5)
    # We can also check the first embedding to be sure
    test_embedding = embeddings.embed_query("test")
    vector_size = len(test_embedding)

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )
    print(f"Collection '{COLLECTION_NAME}' created with vector size {vector_size}.")
else:
    print(f"Collection '{COLLECTION_NAME}' already exists.")

# ----------------------------------------
# Create Vector Store and Add Documents
# ----------------------------------------

# Initialize the VectorStore pointing to the existing collection
vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embedding=embeddings
)

# Add the chunks
print("Adding documents to Qdrant...")
vectorstore.add_documents(chunks)

print("✅ Qdrant collection created and populated successfully!")
print(f"Stored {len(chunks)} chunks.")