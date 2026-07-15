from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from nodes import (
    retrieve_node,
    grade_retrieval_node,
    rewrite_query_node,
    web_search_node,
    decision_node,
    hallucination_checker_node,
    human_review_node,
    finish_node,
    MAX_HALLUCINATION_RETRIES,
)

builder = StateGraph(AgentState)

builder.add_node("retrieve", retrieve_node)
builder.add_node("grade", grade_retrieval_node)
builder.add_node("rewrite", rewrite_query_node)
builder.add_node("web", web_search_node)
builder.add_node("decision", decision_node)
builder.add_node("hallucination", hallucination_checker_node)
builder.add_node("human", human_review_node)
builder.add_node("finish", finish_node)

builder.set_entry_point("retrieve")

builder.add_edge(
    "retrieve",
    "grade",
)


def retrieval_router(state):
    if state["relevant"]:
        return "decision"
    if state["retrieval_attempts"] == 0:
        return "rewrite"
    return "web"


builder.add_conditional_edges(
    "grade",
    retrieval_router,
    {
        "decision": "decision",
        "rewrite": "rewrite",
        "web": "web",
    },
)

builder.add_edge(
    "rewrite",
    "retrieve",
)

builder.add_edge(
    "web",
    "decision",
)

builder.add_edge(
    "decision",
    "hallucination",
)


def hallucination_router(state):
    if state.get("hallucination", False):
        # FIX: previously this unconditionally routed back to
        # "retrieve" with no cap. Since retrieve_node re-queries with
        # the original claim (not the rewritten query), a
        # deterministic LLM would reproduce the same context, the
        # same decision, and the same "ungrounded" verdict every
        # time -- an infinite loop. Confirmed by reproduction: a mock
        # LLM that always returns grounded=False looped hundreds of
        # times with no sign of stopping.
        #
        # Now we cap retries and escalate to a human instead of
        # looping forever.
        if state.get("hallucination_attempts", 0) >= MAX_HALLUCINATION_RETRIES:
            return "human"
        return "retrieve"

    if state["decision"] == "MANUAL_REVIEW":
        return "human"

    return "finish"


builder.add_conditional_edges(
    "hallucination",
    hallucination_router,
    {
        "retrieve": "retrieve",
        "human": "human",
        "finish": "finish",
    },
)

builder.add_edge(
    "human",
    END,
)

builder.add_edge(
    "finish",
    END,
)

memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory,
)