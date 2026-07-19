"""
Lightweight faithfulness + relevancy scoring, without the ragas
dependency chain. Uses the same Groq LLM already configured in llm.py.
"""

from llm import get_llm
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field


class FaithfulnessScore(BaseModel):
    score: float = Field(ge=0, le=1, description="0=not grounded at all, 1=fully grounded")
    reasoning: str


class RelevancyScore(BaseModel):
    score: float = Field(ge=0, le=1, description="0=irrelevant, 1=fully addresses the claim")
    reasoning: str


def evaluate_claim_result(claim: str, result: dict) -> dict:
    context = "\n\n".join(doc["content"] for doc in result.get("retrieved_docs", []))
    answer = f"Decision: {result.get('decision', '')}\n\n{result.get('reasoning', '')}"

    faithfulness_prompt = f"""
Rate how well the ANSWER is supported by the CONTEXT, on a 0-1 scale.
1.0 = every claim in the answer is directly backed by the context.
0.0 = the answer contains claims not found anywhere in the context.

CONTEXT:
{context}

ANSWER:
{answer}
"""
    relevancy_prompt = f"""
Rate how well the ANSWER actually addresses the QUESTION, on a 0-1 scale.
1.0 = directly and completely addresses the question.
0.0 = off-topic or non-responsive.

QUESTION:
{claim}

ANSWER:
{answer}
"""

    llm = get_llm()
    faithfulness = llm.with_structured_output(FaithfulnessScore).invoke(
        [HumanMessage(content=faithfulness_prompt)]
    )
    relevancy = llm.with_structured_output(RelevancyScore).invoke(
        [HumanMessage(content=relevancy_prompt)]
    )

    return {
        "faithfulness": faithfulness.score,
        "faithfulness_reasoning": faithfulness.reasoning,
        "answer_relevancy": relevancy.score,
        "relevancy_reasoning": relevancy.reasoning,
    }
