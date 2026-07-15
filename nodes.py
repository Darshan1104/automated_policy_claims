from langchain_core.messages import HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun

from retriever import retrieve_documents, format_documents
from llm import get_llm

from prompts import (
    RETRIEVAL_GRADER_PROMPT,
    QUERY_REWRITE_PROMPT,
    DECISION_PROMPT,
    HALLUCINATION_PROMPT
)

from state import (
    RetrievalGrade,
    QueryRewrite,
    DecisionOutput,
    HallucinationCheck
)

# Max number of times we'll let the hallucination checker send us
# back to retrieval before giving up and escalating to a human.
MAX_HALLUCINATION_RETRIES = 2

search = DuckDuckGoSearchRun()


def _structured(schema):
    """
    Builds a structured-output model for `schema` using whichever
    Groq key is currently in os.environ (set from the Streamlit
    sidebar). Built fresh per call rather than once at import time,
    since the key may not exist yet when this module is imported.

    .with_retry() also smooths over Groq's llama-3.3-70b-versatile
    occasionally returning "true"/"false" as a string instead of a
    real JSON boolean, which otherwise fails schema validation.
    """
    return get_llm().with_structured_output(schema).with_retry(
        stop_after_attempt=3
    )


def retrieve_node(state):

    print("\n Retrieving Policy Documents...\n")

    query = state["claim"]

    docs = retrieve_documents(query)

    state["retrieved_docs"] = format_documents(docs)

    return state


def grade_retrieval_node(state):

    print("\nGrading Retrieval...\n")

    context = "\n\n".join(
        [
            doc["content"]
            for doc in state["retrieved_docs"]
        ]
    )

    prompt = f"""
{RETRIEVAL_GRADER_PROMPT}

User Claim:
{state["claim"]}

Retrieved Documents:
{context}
"""

    result = _structured(RetrievalGrade).invoke([HumanMessage(content=prompt)])

    print(result)

    state["relevance_score"] = result.relevance_score
    state["relevant"] = result.relevant

    return state


def rewrite_query_node(state):

    print("\n Rewriting Query...\n")

    prompt = f"""
{QUERY_REWRITE_PROMPT}

Original Query:

{state["claim"]}
"""

    result = _structured(QueryRewrite).invoke([HumanMessage(content=prompt)])

    state["rewritten_query"] = result.rewritten_query

    docs = retrieve_documents(result.rewritten_query)

    state["retrieved_docs"] = format_documents(docs)
    state["retrieval_attempts"] += 1
    return state


def web_search_node(state):

    print("\n Searching Regulations Online...\n")

    results = search.invoke(state["claim"])

    state["web_results"] = [results]

    return state


def decision_node(state):

    print("\nMaking Decision...\n")

    context = "\n\n".join(
        [
            doc["content"]
            for doc in state["retrieved_docs"]
        ]
    )

    web_context = "\n\n".join(state.get("web_results", []))
    if web_context:
        context += (
            "\n\nSupplementary Regulatory / Web Search Context:\n"
            + web_context
        )

    prompt = f"""
{DECISION_PROMPT}

User Claim:

{state["claim"]}

Retrieved Policy Documents:

{context}
"""

    result = _structured(DecisionOutput).invoke([HumanMessage(content=prompt)])
    print(result)

    state["decision"] = result.decision
    state["reasoning"] = result.reasoning
    state["citations"] = result.citations

    return state


def hallucination_checker_node(state):

    print("\nChecking Grounding...\n")

    context = "\n\n".join(
        [
            doc["content"]
            for doc in state["retrieved_docs"]
        ]
    )

    prompt = f"""
{HALLUCINATION_PROMPT}

Policy Documents

{context}

Decision

{state["decision"]}

Reasoning

{state["reasoning"]}
"""

    result = _structured(HallucinationCheck).invoke([HumanMessage(content=prompt)])

    print(result)

    state["hallucination"] = not result.grounded

    if state["hallucination"]:
        state["hallucination_attempts"] = state.get("hallucination_attempts", 0) + 1
        print(f"Hallucination detected! (attempt {state['hallucination_attempts']})")

    return state


def human_review_node(state):

    print("\nEscalating to Human...\n")

    state["needs_human"] = True
    state["decision"] = "MANUAL_REVIEW"

    return state


def finish_node(state):

    print("\nWorkflow Complete\n")

    return state