"""
RAGAS evaluation of the agent's final answer vs. its retrieved context.
Run once, after graph.invoke() returns -- kept out of the LangGraph
flow so eval doesn't affect routing/retries.
"""

from datasets import Dataset
from ragas import evaluate as ragas_evaluate
from ragas.metrics import faithfulness, answer_relevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from llm import get_llm, embeddings


def evaluate_claim_result(claim: str, result: dict) -> dict:
    contexts = [doc["content"] for doc in result.get("retrieved_docs", [])]
    if not contexts:
        contexts = ["No policy context was retrieved."]

    answer = f"Decision: {result.get('decision', '')}\n\n{result.get('reasoning', '')}"

    dataset = Dataset.from_dict({
        "question": [claim],
        "answer": [answer],
        "contexts": [contexts],
    })

    ragas_llm = LangchainLLMWrapper(get_llm())
    ragas_embeddings = LangchainEmbeddingsWrapper(embeddings)

    result_scores = ragas_evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
    )

    return result_scores.to_pandas().iloc[0].to_dict()
