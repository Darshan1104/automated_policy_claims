import os
import uuid

import streamlit as st
from graph import graph

st.set_page_config(
    page_title="査定 — Adjudicator",
    page_icon="⚪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# DESIGN TOKENS
# =====================================================================
# Palette (named, not generic):
#   Washi  #F5F1E7  -- paper background
#   Sumi   #22201C  -- ink / primary text
#   Kinari #EDE7D8  -- panel fill, one shade off paper
#   Line   #D9D0BC  -- hairline borders
#   Shu    #B23A2E  -- vermillion, reserved for the seal only
#   Ai     #2E4A63  -- indigo, approve state
#   Take   #5C7A5E  -- bamboo, used sparingly for "ready" states
#   Fade   #8C8474  -- muted secondary text
# Type:
#   Shippori Mincho     -- title, verdict word (2 weights only)
#   Zen Kaku Gothic New -- body copy (2 weights only)
#   IBM Plex Mono       -- case numbers, citations, data (2 weights only)

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@400;700&family=Zen+Kaku+Gothic+New:wght@400;500&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {
    --washi: #F5F1E7;
    --sumi: #22201C;
    --kinari: #EDE7D8;
    --line: #D9D0BC;
    --shu: #B23A2E;
    --ai: #2E4A63;
    --take: #5C7A5E;
    --fade: #8C8474;
}

#MainMenu, footer, header { visibility: hidden; height: 0; }
.block-container {
    padding: 1.6rem 3rem 1rem 3rem !important;
    max-width: 1180px !important;
}

.stApp {
    background: var(--washi);
    color: var(--sumi);
    font-family: 'Zen Kaku Gothic New', sans-serif;
}
h1,h2,h3,label,p,span,div { color: var(--sumi); }

/* ---------- header ---------- */
.top {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--line);
    padding-bottom: 14px;
    margin-bottom: 22px;
}
.title-jp {
    font-family: 'Shippori Mincho', serif;
    font-size: 30px;
    font-weight: 700;
    letter-spacing: 0.02em;
    line-height: 1;
}
.title-en {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: var(--fade);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 4px;
}
.pills { display: flex; gap: 10px; align-items: center; }
.pill {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.04em;
    color: var(--fade);
    background: var(--kinari);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 5px 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    animation: breathe 4.5s ease-in-out infinite;
}
@keyframes breathe {
    0%, 100% { opacity: 0.75; }
    50% { opacity: 1; }
}
.dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.dot.ready { background: var(--take); }
.dot.idle { background: var(--fade); }

/* ---------- panel ---------- */
.panel {
    background: var(--kinari);
    border: 1px solid var(--line);
    border-radius: 3px;
    padding: 26px 28px;
    box-shadow: 0 1px 3px rgba(34,32,28,0.05);
}
.panel-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--fade);
    margin-bottom: 14px;
}
.hr { border: none; border-top: 1px solid var(--line); margin: 18px 0; }

/* ---------- pipeline (quiet, inline dots) ---------- */
.steps { display: flex; gap: 18px; margin-top: 16px; }
.step { display: flex; align-items: center; gap: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; color: var(--fade); }
.step .sd { width: 6px; height: 6px; border-radius: 50%; background: var(--line); transition: background 0.4s ease; }
.step.done .sd { background: var(--ai); }
.step.done { color: var(--sumi); }

/* ---------- ensō (thinking indicator) ---------- */
.enso-wrap { display: flex; justify-content: center; padding: 30px 0 18px 0; }
.enso-circle {
    stroke-dasharray: 620;
    stroke-dashoffset: 620;
    animation: draw 1.6s cubic-bezier(.65,0,.35,1) forwards;
}
@keyframes draw { to { stroke-dashoffset: 40; } }
.enso-caption {
    text-align: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: var(--fade);
    margin-top: -8px;
}

/* ---------- hanko seal ---------- */
.seal-wrap { display: flex; justify-content: center; padding: 8px 0 6px 0; }
.seal {
    width: 108px; height: 108px;
    border: 3px solid var(--shu);
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    transform: rotate(-3deg) scale(1);
    animation: stamp 0.5s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes stamp {
    0% { opacity: 0; transform: rotate(-3deg) scale(1.6); }
    70% { opacity: 1; }
    100% { opacity: 1; transform: rotate(-3deg) scale(1); }
}
.seal-text {
    font-family: 'Shippori Mincho', serif;
    font-weight: 700;
    color: var(--shu);
    font-size: 15px;
    text-align: center;
    line-height: 1.25;
    letter-spacing: 0.03em;
}
.seal.deny { border-color: var(--sumi); }
.seal.deny .seal-text { color: var(--sumi); }
.seal.review { border-color: var(--ai); }
.seal.review .seal-text { color: var(--ai); }

/* ---------- citations ---------- */
.citation {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: var(--sumi);
    padding: 7px 0 7px 14px;
    border-left: 2px solid var(--shu);
    margin-bottom: 6px;
}

/* ---------- reasoning ---------- */
.reasoning-zone {
    max-height: 190px;
    overflow-y: auto;
    line-height: 1.65;
    font-size: 14.5px;
    padding-right: 6px;
}
.reasoning-zone::-webkit-scrollbar { width: 3px; }
.reasoning-zone::-webkit-scrollbar-thumb { background: var(--line); }

/* ---------- rag gauges ---------- */
.gauge-row { display: flex; justify-content: space-between; font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--fade); margin-bottom: 5px; }
.gauge-track { background: var(--washi); border: 1px solid var(--line); border-radius: 2px; height: 5px; overflow: hidden; }
.gauge-fill { height: 100%; transition: width 0.6s ease; }

/* ---------- inputs ---------- */
textarea {
    background: var(--washi) !important;
    color: var(--sumi) !important;
    border: 1px solid var(--line) !important;
    font-family: 'Zen Kaku Gothic New', sans-serif !important;
    font-size: 14.5px !important;
    border-radius: 2px !important;
}
.stButton > button {
    background: var(--sumi) !important;
    color: var(--washi) !important;
    font-family: 'Zen Kaku Gothic New', sans-serif !important;
    font-weight: 500 !important;
    border: none !important;
    border-radius: 2px !important;
    padding: 10px 0 !important;
    width: 100%;
    letter-spacing: 0.03em;
    transition: background 0.2s ease;
}
.stButton > button:hover { background: var(--shu) !important; }
[data-testid="stTextInput"] input {
    background: var(--washi) !important;
    color: var(--sumi) !important;
    border: 1px solid var(--line) !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# SESSION CASE NUMBER
# =====================================================================
if "case_number" not in st.session_state:
    st.session_state.case_number = "CF-" + str(uuid.uuid4())[:8].upper()

# =====================================================================
# HEADER
# =====================================================================
try:
    from retriever import get_collection_status
    kb_ready, kb_count = get_collection_status()
except Exception:
    kb_ready, kb_count = False, 0

kb_dot_class = "ready" if kb_ready else "idle"
kb_label = f"{kb_count} CHUNKS" if kb_ready else "KB IDLE"

st.markdown(f"""
<div class="top">
    <div>
        <div class="title-jp">査定</div>
        <div class="title-en">Claims Adjudicator</div>
    </div>
    <div class="pills">
        <div class="pill"><span class="dot {kb_dot_class}"></span>{kb_label}</div>
        <div class="pill">{st.session_state.case_number}</div>
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
# HELPERS
# =====================================================================
STEP_LABELS = [("retrieve", "Retrieve"), ("grade", "Grade"), ("decision", "Decide"), ("hallucination", "Verify")]

def render_steps(done=None):
    done = done or set()
    out = '<div class="steps">'
    for key, label in STEP_LABELS:
        cls = "step done" if key in done else "step"
        out += f'<div class="{cls}"><span class="sd"></span>{label}</div>'
    out += "</div>"
    return out

def gauge(label, value):
    pct = max(0, min(100, round(value * 100)))
    color = "var(--take)" if pct >= 70 else ("var(--ai)" if pct >= 40 else "var(--shu)")
    st.markdown(f"""
    <div class="gauge-row"><span>{label}</span><span>{value:.2f}</span></div>
    <div class="gauge-track"><div class="gauge-fill" style="width:{pct}%; background:{color};"></div></div>
    """, unsafe_allow_html=True)

ENSO_SVG = """
<div class="enso-wrap">
<svg width="120" height="120" viewBox="0 0 220 220">
    <circle class="enso-circle" cx="110" cy="110" r="88" fill="none" stroke="#22201C" stroke-width="7" stroke-linecap="round"/>
</svg>
</div>
"""

# =====================================================================
# MAIN LAYOUT -- two quiet panels, generous margin between
# =====================================================================
col_left, col_right = st.columns([1, 1.15], gap="large")

with col_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Statement of Loss</div>', unsafe_allow_html=True)
    claim = st.text_area(
        "Statement of loss",
        height=190,
        label_visibility="collapsed",
        placeholder="Describe what happened, when, and what was damaged or lost..."
    )
    submitted = st.button("File Claim")
    st.markdown("</div>", unsafe_allow_html=True)

result_slot = col_right.empty()

def draw_idle():
    with result_slot.container():
        st.markdown('<div class="panel" style="min-height:420px; display:flex; flex-direction:column; justify-content:center;">', unsafe_allow_html=True)
        st.markdown("""
        <div class="enso-wrap">
        <svg width="110" height="110" viewBox="0 0 220 220">
            <circle cx="110" cy="110" r="88" fill="none" stroke="#D9D0BC" stroke-width="4" stroke-dasharray="6 10" stroke-linecap="round"/>
        </svg>
        </div>
        <div class="enso-caption">Awaiting a claim</div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

if not submitted:
    draw_idle()

if submitted:

    if not os.environ.get("GROQ_API_KEY"):
        st.error("Enter your Groq API key via ⚙ above before filing a claim.")
        draw_idle()
        st.stop()

    if not claim.strip():
        st.warning("Enter a statement of loss before filing the claim.")
        draw_idle()
        st.stop()

    with result_slot.container():
        st.markdown('<div class="panel" style="min-height:420px;">', unsafe_allow_html=True)
        st.markdown(ENSO_SVG, unsafe_allow_html=True)
        st.markdown('<div class="enso-caption">Reading the policy...</div>', unsafe_allow_html=True)
        st.markdown(render_steps(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

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

    try:
        result = graph.invoke(initial_state, config=config)

        decision = result.get("decision", "MANUAL_REVIEW")
        reasoning = result.get("reasoning", "No reasoning provided.")
        citations = result.get("citations", [])
        needs_human = result.get("needs_human", False)

        seal_class = {"APPROVE": "", "DENY": "deny"}.get(decision, "review")
        seal_text = {"APPROVE": "承認<br>Approved", "DENY": "却下<br>Denied"}.get(decision, "審査中<br>Manual<br>Review")

        with result_slot.container():
            st.markdown('<div class="panel">', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="seal-wrap">
                <div class="seal {seal_class}"><div class="seal-text">{seal_text}</div></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(render_steps({"retrieve", "grade", "decision", "hallucination"}), unsafe_allow_html=True)
            if needs_human:
                st.caption("⚠ Escalated for manual adjuster review.")

            st.markdown('<hr class="hr">', unsafe_allow_html=True)
            st.markdown('<div class="panel-label">Case Notes</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="reasoning-zone">{reasoning}</div>', unsafe_allow_html=True)

            st.markdown('<hr class="hr">', unsafe_allow_html=True)
            st.markdown('<div class="panel-label">Policy Citations</div>', unsafe_allow_html=True)
            if citations:
                for c in citations:
                    st.markdown(f'<div class="citation">{c}</div>', unsafe_allow_html=True)
            else:
                st.caption("No specific citations found.")

            st.markdown('<hr class="hr">', unsafe_allow_html=True)
            st.markdown('<div class="panel-label">RAG Quality</div>', unsafe_allow_html=True)
            try:
                from ragas_eval import evaluate_claim_result
                scores = evaluate_claim_result(claim, result)
                gc1, gc2 = st.columns(2)
                with gc1:
                    gauge("Faithfulness", scores.get("faithfulness", 0))
                with gc2:
                    gauge("Relevancy", scores.get("answer_relevancy", 0))
            except Exception as e:
                st.caption(f"Scoring unavailable: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

    except KeyError as e:
        with result_slot.container():
            st.error(f"Graph returned an incomplete state. Missing key: {e}")
    except Exception as e:
        with result_slot.container():
            st.error(f"An unexpected error occurred: {e}")
