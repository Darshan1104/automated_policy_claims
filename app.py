import os
import uuid
import time

import streamlit as st
from graph import graph

st.set_page_config(
    page_title="Claims Case File",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# DESIGN TOKENS + GLOBAL STYLE
# =====================================================================
# Palette:
#   Ink Navy   #14202E  -- app background
#   Panel      #1C2B3C  -- cards / containers
#   Panel Line #2E4258  -- borders / dividers
#   Parchment  #EDE6D6  -- primary text on dark
#   Muted      #93A2B4  -- secondary text
#   Brass      #C68A2E  -- APPROVE stamp
#   Brick      #A23E3E  -- DENY stamp
#   Slate      #5B7A9D  -- MANUAL REVIEW stamp / pending state
# Type:
#   Display -> Source Serif 4 (case-file, legal-document weight)
#   Mono    -> IBM Plex Mono (citations, case numbers, ledger data)
#   UI      -> Inter (chrome, labels, buttons)

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {
    --ink-navy: #14202E;
    --panel: #1C2B3C;
    --panel-line: #2E4258;
    --parchment: #EDE6D6;
    --muted: #93A2B4;
    --brass: #C68A2E;
    --brick: #A23E3E;
    --slate: #5B7A9D;
}

/* ---------- base ---------- */
.stApp {
    background: var(--ink-navy);
    color: var(--parchment);
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background: #101A25;
    border-right: 1px solid var(--panel-line);
}
[data-testid="stSidebar"] * { color: var(--parchment) !important; }

h1, h2, h3 {
    font-family: 'Source Serif 4', serif !important;
    color: var(--parchment) !important;
    letter-spacing: 0.01em;
}
p, label, span, div { color: var(--parchment); }

hr { border-color: var(--panel-line) !important; }

/* ---------- folder tab (sidebar header) ---------- */
.folder-tab {
    background: var(--panel);
    border: 1px solid var(--panel-line);
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 10px 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.08em;
    color: var(--muted);
    text-transform: uppercase;
}

/* ---------- case header ---------- */
.case-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 2px solid var(--panel-line);
    padding-bottom: 14px;
    margin-bottom: 6px;
}
.case-title {
    font-family: 'Source Serif 4', serif;
    font-size: 34px;
    font-weight: 700;
    margin: 0;
}
.case-number {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    color: var(--muted);
    letter-spacing: 0.05em;
}

/* ---------- panel / card ---------- */
.panel {
    background: var(--panel);
    border: 1px solid var(--panel-line);
    border-radius: 8px;
    padding: 20px 22px;
    margin-bottom: 16px;
}
.panel-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
}

/* ---------- pipeline trace ---------- */
.trace-row {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    padding: 5px 0;
    color: var(--muted);
}
.trace-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--panel-line);
    flex-shrink: 0;
}
.trace-row.done .trace-dot { background: var(--brass); }
.trace-row.done { color: var(--parchment); }

/* ---------- stamp ---------- */
.stamp-wrap { display: flex; justify-content: center; padding: 18px 0 6px 0; }
.stamp {
    font-family: 'Source Serif 4', serif;
    font-weight: 700;
    font-size: 26px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border: 4px solid currentColor;
    border-radius: 10px;
    padding: 14px 30px;
    transform: rotate(-4deg);
    display: inline-block;
    opacity: 0.92;
}
.stamp.approve { color: var(--brass); }
.stamp.deny { color: var(--brick); }
.stamp.review { color: var(--slate); }

/* ---------- citation card ---------- */
.citation {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    background: #16222F;
    border-left: 3px solid var(--slate);
    padding: 8px 12px;
    margin-bottom: 8px;
    border-radius: 0 4px 4px 0;
    color: var(--parchment);
}

/* ---------- gauge ---------- */
.gauge-label {
    display: flex; justify-content: space-between;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 4px;
}
.gauge-track {
    background: #101A25;
    border-radius: 4px;
    height: 8px;
    overflow: hidden;
    border: 1px solid var(--panel-line);
}
.gauge-fill { height: 100%; border-radius: 4px; }

/* ---------- buttons ---------- */
.stButton > button {
    background: var(--brass) !important;
    color: #14202E !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 10px 22px !important;
    letter-spacing: 0.02em;
}
.stButton > button:hover { filter: brightness(1.08); }

textarea {
    background: #101A25 !important;
    color: var(--parchment) !important;
    border: 1px solid var(--panel-line) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 14px !important;
}

/* ---------- misc streamlit overrides ---------- */
[data-testid="stMetricValue"] { color: var(--parchment) !important; font-family: 'IBM Plex Mono', monospace; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; }
.stAlert { border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# SESSION CASE NUMBER
# =====================================================================
if "case_number" not in st.session_state:
    st.session_state.case_number = "CF-" + str(uuid.uuid4())[:8].upper()

# =====================================================================
# SIDEBAR -- "CASE INTAKE"
# =====================================================================
with st.sidebar:
    st.markdown('<div class="folder-tab">📁 Case Intake</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel" style="border-radius:0 0 8px 8px; margin-top:0;">', unsafe_allow_html=True)

    st.markdown('<div class="panel-label">Groq API Key</div>', unsafe_allow_html=True)
    api_key_input = st.text_input(
        "Groq API key",
        type="password",
        label_visibility="collapsed",
        help="Get a free key at https://console.groq.com/keys. Kept only in this session, not saved anywhere."
    )
    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">📚 Knowledge Base</div>', unsafe_allow_html=True)
    try:
        from retriever import get_collection_status
        ready, count = get_collection_status()
        if ready:
            st.success(f"{count} policy chunks loaded")
        else:
            st.info(
                "No policy documents loaded yet — they'll be ingested "
                "automatically from data/policies/ on your first claim."
            )
    except Exception:
        st.info("Knowledge base status unavailable yet.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Case Reference</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="case-number">{st.session_state.case_number}</div>',
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# MAIN -- "CASE FILE"
# =====================================================================
st.markdown(f"""
<div class="case-header">
    <p class="case-title">🗂️ Claims Case File</p>
    <p class="case-number">{st.session_state.case_number}</p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<p style="color:var(--muted); margin-top:-4px;">'
    'AI-assisted claim adjudication — LangGraph &middot; Qdrant &middot; Groq'
    '</p>',
    unsafe_allow_html=True
)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-label">Statement of Loss</div>', unsafe_allow_html=True)
claim = st.text_area(
    "Statement of loss",
    height=160,
    label_visibility="collapsed",
    placeholder="Describe what happened, when, and what was damaged or lost..."
)
submitted = st.button("File Claim →")
st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# PIPELINE TRACE (static reference of the graph path)
# =====================================================================
TRACE_STEPS = [
    ("retrieve", "Retrieve policy documents"),
    ("grade", "Grade retrieval relevance"),
    ("decision", "Render decision"),
    ("hallucination", "Verify grounding"),
]

def render_trace(done_keys=None):
    done_keys = done_keys or set()
    rows = ""
    for key, label in TRACE_STEPS:
        cls = "trace-row done" if key in done_keys else "trace-row"
        mark = "✓" if key in done_keys else "·"
        rows += f'<div class="{cls}"><span class="trace-dot"></span>{mark}  {label}</div>'
    return rows

if submitted:

    if not os.environ.get("GROQ_API_KEY"):
        st.error("Enter your Groq API key in the sidebar before filing a claim.")
        st.stop()

    if not claim.strip():
        st.warning("Enter a statement of loss before filing the claim.")
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

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    col_trace, col_status = st.columns([1, 2])
    with col_trace:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Pipeline Trace</div>', unsafe_allow_html=True)
        trace_placeholder = st.empty()
        trace_placeholder.markdown(render_trace(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_status:
        status_placeholder = st.empty()
        status_placeholder.info("Processing claim through the adjudication pipeline...")

    try:
        result = graph.invoke(initial_state, config=config)

        trace_placeholder.markdown(
            render_trace({"retrieve", "grade", "decision", "hallucination"}),
            unsafe_allow_html=True
        )
        status_placeholder.empty()

        decision = result.get("decision", "MANUAL_REVIEW")
        reasoning = result.get("reasoning", "No reasoning provided.")
        citations = result.get("citations", [])
        needs_human = result.get("needs_human", False)

        stamp_class = {
            "APPROVE": "approve",
            "DENY": "deny",
        }.get(decision, "review")

        stamp_label = {
            "APPROVE": "Approved",
            "DENY": "Denied",
        }.get(decision, "Manual Review")

        st.markdown('<div class="stamp-wrap">', unsafe_allow_html=True)
        st.markdown(f'<div class="stamp {stamp_class}">{stamp_label}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if needs_human:
            st.warning("This case has been escalated for manual adjuster review.")

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Case Notes (Reasoning)</div>', unsafe_allow_html=True)
        st.write(reasoning)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Policy Citations</div>', unsafe_allow_html=True)
        if citations:
            for c in citations:
                st.markdown(f'<div class="citation">{c}</div>', unsafe_allow_html=True)
        else:
            st.write("No specific policy citations found.")
        st.markdown("</div>", unsafe_allow_html=True)

        # -----------------------------------------------------------
        # RAGAS / lightweight faithfulness + relevancy scoring
        # -----------------------------------------------------------
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">🧪 RAG Quality</div>', unsafe_allow_html=True)
        with st.spinner("Scoring the answer against retrieved policy context..."):
            try:
                from ragas_eval import evaluate_claim_result
                scores = evaluate_claim_result(claim, result)

                def gauge(label, value):
                    pct = max(0, min(100, round(value * 100)))
                    color = "var(--brass)" if pct >= 70 else ("var(--slate)" if pct >= 40 else "var(--brick)")
                    st.markdown(f"""
                    <div class="gauge-label"><span>{label}</span><span>{value:.2f}</span></div>
                    <div class="gauge-track"><div class="gauge-fill" style="width:{pct}%; background:{color};"></div></div>
                    """, unsafe_allow_html=True)

                gc1, gc2 = st.columns(2)
                with gc1:
                    gauge("Faithfulness", scores.get("faithfulness", 0))
                with gc2:
                    gauge("Answer Relevancy", scores.get("answer_relevancy", 0))

                if scores.get("faithfulness", 1) < 0.7:
                    st.warning(
                        "Faithfulness is low — the reasoning may include claims "
                        "not backed by the retrieved policy text."
                    )
            except Exception as e:
                st.info(f"RAG quality scoring unavailable: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    except KeyError as e:
        status_placeholder.empty()
        st.error(f"Error: the graph returned an incomplete state. Missing key: {e}")
        st.info("Ensure all nodes in your graph return the full state dictionary.")
    except Exception as e:
        status_placeholder.empty()
        st.error(f"An unexpected error occurred: {e}")

else:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Pipeline Trace</div>', unsafe_allow_html=True)
    st.markdown(render_trace(), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
