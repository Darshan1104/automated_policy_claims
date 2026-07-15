"""
Shared state for the LangGraph workflow.
"""

from typing import List, TypedDict, Dict
from pydantic import BaseModel, Field, field_validator


# =====================================================
# LangGraph State
# =====================================================

class AgentState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """

    # User Input
    claim: str

    # Query
    rewritten_query: str

    # Retrieved policy chunks
    retrieved_docs: List[Dict]

    # DuckDuckGo results
    web_results: List[str]

    # Retrieval quality
    relevance_score: float

    # Final decision
    decision: str

    # Explanation for audit
    reasoning: str

    # Source references
    citations: List[str]

    # Human escalation
    needs_human: bool

    retrieval_attempts: int

    relevant: bool

    hallucination: bool

    # Counts how many times the hallucination checker has sent us
    # back to retrieve, so graph.py can stop looping and escalate
    # to a human instead of retrying forever.
    hallucination_attempts: int


class RetrievalGrade(BaseModel):

    relevant: bool = Field(
        description="Whether retrieved documents answer the question."
    )

    relevance_score: float = Field(
        ge=0,
        le=1,
        description="Score between 0 and 1"
    )

    reasoning: str

    @field_validator("relevant", mode="before")
    @classmethod
    def _coerce_relevant(cls, v):
        # FIX: Groq's llama-3.3-70b-versatile occasionally returns
        # "true"/"false" as a string instead of a JSON boolean, which
        # fails schema validation before LangChain even parses it.
        # This is a backstop alongside .with_retry() in nodes.py.
        if isinstance(v, str):
            return v.strip().lower() in ("true", "yes", "1")
        return v


class DecisionOutput(BaseModel):

    decision: str = Field(
        description="APPROVE, DENY or MANUAL_REVIEW"
    )

    reasoning: str
    confidence: float = Field(
        ge=0,
        le=1
    )
    citations: List[str]


class HallucinationCheck(BaseModel):

    grounded: bool

    reasoning: str

    @field_validator("grounded", mode="before")
    @classmethod
    def _coerce_grounded(cls, v):
        if isinstance(v, str):
            return v.strip().lower() in ("true", "yes", "1")
        return v


class QueryRewrite(BaseModel):

    rewritten_query: str