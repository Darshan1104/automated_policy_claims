from nodes import retrieve_node, decision_node, hallucination_checker_node
state = {
    "claim":"My basement flooded after a burst pipe.",
    "retrieved_docs":[],
    "rewritten_query":"",
    "web_results":[],
    "relevance_score":0,
    "decision":"",
    "reasoning":"",
    "citations":[],
    # "confidence":0,
    "needs_human":False}


state = retrieve_node(state)

state = decision_node(state)

print(state["decision"])

print(state["reasoning"])

print(state["citations"])