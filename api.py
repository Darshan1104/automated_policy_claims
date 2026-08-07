"""
FastAPI wrapper around the LangGraph claims-adjudication agent.

Same graph.py / nodes.py the Streamlit app uses -- this just exposes
it as an HTTP API instead of a UI, so it can be containerized and put
behind a real cloud endpoint for deployment + load testing.

Run locally:
    uvicorn api:app --reload --port 8080

Endpoints:
    GET  /health       -- readiness check (Qdrant + Groq key configured)
    POST /adjudicate    -- run a claim through the agent
"""

import os
import time
import uuid
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph import graph
from retriever import get_collection_status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("claims-api")

app = FastAPI(
    title="Insurance Claims Adjudication API",
    version="1.0.0",
)


# ---------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------

class ClaimRequest(BaseModel):
    claim: str = Field(..., min_length=1, description="Statement of loss / claim text")


class ClaimResponse(BaseModel):
    case_number: str
    decision: str
    reasoning: str
    citations: List[str]
    needs_human: bool
    latency_ms: int


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/health")
def health():
    """
    Used by the cloud platform's health probe, and by you to confirm
    the deployed container can actually reach Qdrant and has a Groq
    key configured -- before you start throwing load at it.
    """
    try:
        ready, count = get_collection_status()
    except Exception as e:
        return {"status": "degraded", "qdrant_ready": False, "error": str(e)}

    groq_configured = bool(os.getenv("GROQ_API_KEY"))

    return {
        "status": "ok" if (ready and groq_configured) else "degraded",
        "qdrant_ready": ready,
        "chunks_loaded": count,
        "groq_configured": groq_configured,
    }


# ---------------------------------------------------------
# Core endpoint
# ---------------------------------------------------------

@app.post("/adjudicate", response_model=ClaimResponse)
def adjudicate(request: ClaimRequest):
    """
    Runs a single claim through the full LangGraph pipeline
    (retrieve -> grade -> [rewrite/web] -> decision -> hallucination
    check -> finish/human) and returns the final decision.

    Synchronous def on purpose: FastAPI runs sync endpoints in a
    threadpool automatically, so this doesn't block the event loop
    even though graph.invoke() itself is blocking (LLM calls,
    Qdrant calls). That's what lets /health stay responsive under
    load in the load test.
    """
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not configured on server")

    case_number = "CF-" + str(uuid.uuid4())[:8].upper()

    initial_state = {
        "claim": request.claim,
        "rewritten_query": "",
        "retrieved_docs": [],
        "web_results": [],
        "relevance_score": 0,
        "relevant": False,
        "retrieval_attempts": 0,
        "hallucination": False,
        "hallucination_attempts": 0,
        "decision": "",
        "reasoning": "",
        "citations": [],
        "needs_human": False,
    }
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    start = time.monotonic()
    try:
        result = graph.invoke(initial_state, config=config)
    except Exception as e:
        logger.exception(f"[{case_number}] graph invocation failed")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")
    latency_ms = int((time.monotonic() - start) * 1000)

    logger.info(
        f"[{case_number}] decision={result.get('decision')} "
        f"latency_ms={latency_ms} needs_human={result.get('needs_human')}"
    )

    return ClaimResponse(
        case_number=case_number,
        decision=result.get("decision", "MANUAL_REVIEW"),
        reasoning=result.get("reasoning", ""),
        citations=result.get("citations", []),
        needs_human=result.get("needs_human", False),
        latency_ms=latency_ms,
    )