import os
import uuid

import streamlit as st
from graph import graph

st.set_page_config(
    page_title="Insurance Claims Adjudication Agent",
    page_icon="🏥",
    layout="wide"
)

# NEW: Groq API key entry in the sidebar. Stored in os.environ for
# this process only -- not written to disk. llm.py's get_llm() reads
# it lazily the first time a node actually needs the model, so this
# import at the top of the file (graph -> nodes -> llm) never fails
# just because the key hasn't been entered yet.
with st.sidebar:
    st.subheader("🔑 Groq API Key")
    api_key_input = st.text_input(
        "Enter your Groq API key",
        type="password",
        #value=os.environ.get("GROQ_API_KEY", ""),
        help="Get a free key at https://console.groq.com/keys. "
             "Kept only in this session, not saved anywhere."
    )
    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input

st.title("🏥 Insurance Claims Adjudication Agent")

st.write(
    "AI-powered insurance claim evaluation using LangGraph + Qdrant + Groq"
)

claim = st.text_area(
    "Enter Insurance Claim",
    height=180
)

if st.button("Evaluate Claim"):

    if not os.environ.get("GROQ_API_KEY"):
        st.error("Please enter your Groq API key in the sidebar first.")
        st.stop()

    initial_state = {
        "claim": claim,
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
        "needs_human": False
    }

    # Fresh thread_id per submission so separate claims don't share
    # checkpoint state.
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    try:
        result = graph.invoke(
            initial_state,
            config=config
        )

        st.divider()

        st.subheader("Decision")
        decision = result.get("decision", "No decision made")
        st.success(decision)

        st.subheader("Reasoning")
        st.write(result.get("reasoning", "No reasoning provided."))

        st.subheader("Policy Citations")
        citations = result.get("citations", [])
        if citations:
            for citation in citations:
                st.write("•", citation)
        else:
            st.write("No specific policy citations found.")

        if result.get("needs_human", False):
            st.warning(
                "Manual review required."
            )

    except KeyError as e:
        st.error(f"Error: The graph returned an incomplete state. Missing key: {e}")
        st.info("Ensure all nodes in your graph return the full state dictionary.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")