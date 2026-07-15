"""
Centralized AI resources.

Every other file imports objects from here instead of
creating new LLMs or embedding models.
"""

import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

load_dotenv()  # still works as a fallback if you keep using a .env file

# ---------------------------------------------------
# Embeddings + local Qdrant client
# ---------------------------------------------------
# These don't need a Groq key, so they stay eager.

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)

qdrant_client = QdrantClient(
    url="https://59552c81-d1a3-46d7-ace6-03db960e6505.eu-west-1-0.aws.cloud.qdrant.io",
    api_key=os.environ["QDRANT_API_KEY"],
)

# ---------------------------------------------------
# Groq LLM -- built lazily
# ---------------------------------------------------
# FIX: previously ChatGroq(...) was constructed the moment this module
# was imported, and raised ValueError immediately if GROQ_API_KEY
# wasn't set. Since `app.py` imports graph -> nodes -> llm at the top
# of the file, that meant the app crashed before Streamlit could even
# render a field to type the key into.
#
# get_llm() defers construction until a node actually needs the LLM
# (i.e. after the "Evaluate Claim" button is clicked), and rebuilds
# the client automatically if the key in os.environ changes -- so
# pasting a new key into the sidebar picks up immediately.

_llm_cache = {"key": None, "instance": None}


def get_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Enter your Groq API key in the "
            "sidebar before evaluating a claim."
        )

    if _llm_cache["key"] != api_key:
        _llm_cache["instance"] = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0,
        )
        _llm_cache["key"] = api_key

    return _llm_cache["instance"]
