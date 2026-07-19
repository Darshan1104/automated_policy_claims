import os
import uuid

import streamlit as st
from graph import graph

st.set_page_config(
    page_title="Claims Adjudicator",
    page_icon="🗂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# DESIGN TOKENS
# =====================================================================
# One family (Inter), used with real hierarchy, so nothing has to
# fight for attention. Mono (JetBrains Mono) reserved for case
# numbers and citations only.
#
# Type scale:
#   Page title      26px / 700
#   Section eyebrow  12.5px / 600, uppercase, tracked
#   Body / reasoning 15.5px / 400, line-height 1.65
#   Verdict word     22px / 700
#   Stat number      30px / 700
#
# Color:
#   Ink       #14161A  primary text
#   Muted     #6B7280  secondary text
#   Border    #E5E7EB
#   Surface   #FFFFFF
#   Canvas    #FAFAFA
#   Accent    #4F46E5  primary actions
#   Approve   text #15803D  bg #ECFDF3  border #86EFAC
#   Deny      text #B91C1C  bg #FEF2F2  border #FCA5A5
#   Review    text #B45309  bg #FFFBEB  border #FDE68A

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {
    --ink: #14161A;
    --muted: #6B7280;
    --border: #E5E7EB;
    --surface: #FFFFFF;
    --canvas: #FAFAFA;
    --accent: #4F46E5;
    --accent-soft: #EEF2FF;
}

#MainMenu, footer, header { visibility: hidden; height: 0; }
.block-container {
    padding: 2.2rem 1.5rem 3rem 1.5rem !important;
    max-width: 820px !important;
}
.stApp { background: var(--canvas); font-family: 'Inter', sans-serif; }
h1,h2,h3,p,span,div,label { color: var(--ink); }

/* ---------- top bar ---------- */
.top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 28px;
}
.page-title { font-size: 22px; font-weight: 700; letter-spacing: -0.01em; }
.page-sub { font-size: 13px; color: var(--muted); margin-top: 2px; }
.meta {
    display: flex; gap: 10px; align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    color: var(--muted);
}
.kb-chip {
    display: flex; align-items: center; gap: 6px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 5px 11px;
}
.kb-dot { width: 6px; height: 6px; border-radius: 50%; }
.kb-dot.ready { background: #15803D; }
.kb-dot.idle { background: var(--muted); }

/* ---------- card ---------- */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px 26px;
    margin-bottom: 18px;
    box-shadow: 0 1px 2px rgba(20,22,26,0.04);
}
.eyebrow {
    font-size: 12.5px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
}
.hint {
    font-size: 13.5px;
    color: var(--muted);
    font-style: italic;
    text-align: center;
    padding: 6px 0 2px 0;
}

/* ---------- live pipeline timeline ---------- */
@keyframes slideIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
}
.tl-row {
    display: flex; align-items: center; gap: 10px;
    font-size: 14px;
    padding: 6px 0;
    animation: slideIn 0.3s ease;
}
.tl-check {
    width: 18px; height: 18px; border-radius: 50%;
    background: var(--accent-soft); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; flex-shrink: 0;
}

/* ---------- verdict banner ---------- */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.verdict {
    display: flex; align-items: center; gap: 14px;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 18px;
    animation: fadeUp 0.4s ease;
}
.verdict.approve { background: #ECFDF3; border: 1px solid #86EFAC; }
.verdict.deny { background: #FEF2F2; border: 1px solid #FCA5A5; }
.verdict.review { background: #FFFBEB; border: 1px solid #FDE68A; }
.verdict-icon { font-size: 26px; line-height: 1; }
.verdict-word {
    font-size: 21px; font-weight: 700; letter-spacing: -0.01em;
}
.verdict.approve .verdict-word { color: #15803D; }
.verdict.deny .verdict-word { color: #B91C1C; }
.verdict.review .verdict-word { color: #B45309; }
.verdict-case {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; color: var(--muted); margin-top: 2px;
}

/* ---------- reasoning ---------- */
.reasoning {
    font-size: 15.5px;
    line-height: 1.65;
    color: var(--ink);
    max-height: 320px;
    overflow-y: auto;
    padding-right: 4px;
}
.reasoning::-webkit-scrollbar { width: 4px; }
.reasoning::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ---------- citations ---------- */
.citation-chip {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    background: var(--accent-soft);
    color: var(--accent);
    border-radius: 6px;
    padding: 6px 10px;
    margin: 0 6px 6px 0;
}

/* ---------- stat cards ---------- */
.stat-grid { display: flex; gap: 14px; }
.stat-card {
    flex: 1;
    background: var(--canvas);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
}
.stat-label { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-track { background: var(--border); border-radius: 3px; height: 5px; overflow: hidden; margin-top: 8px; }
.stat-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }

/* ---------- form controls ---------- */
textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    color: var(--ink) !important;
}
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    border: none !important;
    border-radius: 8px !important;
    height: 44px !important;
    padding: 0 22px !important;
}
.stButton > button:hover { background: #4338CA !important; }
[data-testid="stTextInput"] input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# SESSION CASE NUMBER
# =====================================================================
if "case_number" not in st.session_state:
    st.session_state.case_number = "CF-" + str(uuid.uuid4())[:8].upper()

# =====================================================================
# TOP BAR
# =====================================================================
try:
    from retriever import get_collection_status
    kb_ready, kb_count = get_collection_status()
except Exception:
    kb_ready, kb_count = False, 0

kb_dot = "ready" if kb_ready else "idle"
kb_label = f"{kb_count} chunks loaded" if kb_ready else "KB idle"

st.markdown(f"""
<div class="top">
    <div>
        <div class="page-title">Claims Adjudicator</div>
        <div class="page-sub">AI-assisted policy claim evaluation</div>
    </div>
    <div class="meta">
        <div class="kb-chip"><span class="kb-dot {kb_dot}"></span>{kb_label}</div>
        <div class="kb-chip">{st.session_state.case_number}</div>
    </div>
</div>
""", unsafe_allow_html=True)

try:
    key_ctx = st.popover("⚙ Groq API key")
except AttributeError:
    key_ctx = st.expander("⚙ Groq API key")

with key_ctx:
    api_key_input = st.text_input(
        "Groq API key",
        type="password",
        help="Get a free key at https://console.groq.com/keys. Kept only in this session."
    )
    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input

# =====================================================================
# NODE LABELS FOR THE LIVE STREAM
# =====================================================================
NODE_LABELS = {
    "retrieve": "Retrieving policy documents",
    "grade": "Grading retrieval relevance",
    "rewrite": "Rewriting search query",
    "web": "Searching web for context",
    "decision": "Rendering decision",
    "hallucination": "Verifying grounding",
    "human": "Escalating to human review",
    "finish": "Finalizing",
}

def render_timeline(steps):
    rows = ""
    for i, key in enumerate(steps, start=1):
        label = NODE_LABELS.get(key, key)
        rows += f'<div class="tl-row"><span class="tl-check">✓</span>{label}</div>'
    return rows

def gauge_card(label, value):
    pct = max(0, min(100, round(value * 100)))
    color = "#15803D" if pct >= 70 else ("#B45309" if pct >= 40 else "#B91C1C")
    return f"""
    <div class="stat-card">
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value:.2f}</div>
        <div class="stat-track"><div class="stat-fill" style="width:{pct}%; background:{color};"></div></div>
    </div>
    """

# =====================================================================
# INPUT CARD
# =====================================================================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">Statement of Loss</div>', unsafe_allow_html=True)
claim = st.text_area(
    "Statement of loss",
    height=150,
    label_visibility="collapsed",
    placeholder="Describe what happened, when, and what was damaged or lost..."
)
submitted = st.button("File Claim")
st.markdown("</div>", unsafe_allow_html=True)

if not submitted:
    st.markdown('<p class="hint">Your case analysis will appear here once a claim is filed.</p>', unsafe_allow_html=True)

# =====================================================================
# PROCESS + LIVE RESULTS
# =====================================================================
if submitted:

    if not os.environ.get("GROQ_API_KEY"):
        st.error("Enter your Groq API key via ⚙ above before filing a claim.")
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
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    timeline_slot = st.empty()
    completed_steps = []
    accumulated_state = dict(initial_state)

    try:
        with timeline_slot.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="eyebrow">Pipeline</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        for step_output in graph.stream(initial_state, config=config):
            for node_name, node_state in step_output.items():
                if isinstance(node_state, dict):
                    accumulated_state.update(node_state)
                completed_steps.append(node_name)
                with timeline_slot.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div class="eyebrow">Pipeline</div>', unsafe_allow_html=True)
                    st.markdown(render_timeline(completed_steps), unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        result = accumulated_state

        decision = result.get("decision", "MANUAL_REVIEW")
        reasoning = result.get("reasoning", "No reasoning provided.")
        citations = result.get("citations", [])
        needs_human = result.get("needs_human", False)

        verdict_class = {"APPROVE": "approve", "DENY": "deny"}.get(decision, "review")
        verdict_icon = {"APPROVE": "✅", "DENY": "⛔"}.get(decision, "🔎")
        verdict_word = {"APPROVE": "Approved", "DENY": "Denied"}.get(decision, "Manual Review")

        st.markdown(f"""
        <div class="verdict {verdict_class}">
            <div class="verdict-icon">{verdict_icon}</div>
            <div>
                <div class="verdict-word">{verdict_word}</div>
                <div class="verdict-case">{st.session_state.case_number}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if needs_human:
            st.warning("This case has been escalated for manual adjuster review.")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Case Notes</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="reasoning">{reasoning}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if citations:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="eyebrow">Policy Citations</div>', unsafe_allow_html=True)
            chips = "".join(f'<span class="citation-chip">{c}</span>' for c in citations)
            st.markdown(chips, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">RAG Quality</div>', unsafe_allow_html=True)
        try:
            from ragas_eval import evaluate_claim_result
            scores = evaluate_claim_result(claim, result)
            st.markdown(
                '<div class="stat-grid">'
                + gauge_card("Faithfulness", scores.get("faithfulness", 0))
                + gauge_card("Answer Relevancy", scores.get("answer_relevancy", 0))
                + '</div>',
                unsafe_allow_html=True
            )
        except Exception as e:
            st.caption(f"Scoring unavailable: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    except KeyError as e:
        st.error(f"Graph returned an incomplete state. Missing key: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
