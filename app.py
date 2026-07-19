import os
import uuid

import streamlit as st
from graph import graph

st.set_page_config(
    page_title="ADJUDICATOR // CASE HUD",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# DESIGN TOKENS
# =====================================================================
# Palette:
#   Void       #05080D  -- background
#   Panel      rgba(10,22,34,.55) w/ blur -- glass HUD panels
#   Cyan       #00E5FF  -- primary readout / active state
#   Amber      #FFB020  -- caution / manual review
#   Green      #39FF9E  -- approve
#   Red        #FF3B4E  -- deny
#   Ice        #D9F4FF  -- primary text
#   Dim        #4F6B7A  -- inactive / muted
# Type:
#   Orbitron      -- HUD headers, labels, verdict ring
#   IBM Plex Mono -- data, citations, case numbers
#   Inter         -- body copy

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {
    --void: #05080D;
    --panel: rgba(10, 22, 34, 0.55);
    --panel-line: rgba(0, 229, 255, 0.28);
    --cyan: #00E5FF;
    --amber: #FFB020;
    --green: #39FF9E;
    --red: #FF3B4E;
    --ice: #D9F4FF;
    --dim: #4F6B7A;
}

#MainMenu, footer, header { visibility: hidden; height: 0; }
.block-container {
    padding: 0.6rem 1.2rem 0.4rem 1.2rem !important;
    max-width: 100% !important;
}

.stApp {
    background:
        radial-gradient(ellipse at 50% -10%, rgba(0,229,255,0.08), transparent 55%),
        repeating-linear-gradient(0deg, rgba(0,229,255,0.025) 0px, rgba(0,229,255,0.025) 1px, transparent 1px, transparent 3px),
        var(--void);
    color: var(--ice);
    font-family: 'Inter', sans-serif;
}

h1,h2,h3,h4,label,p,span,div { color: var(--ice); }

/* ---------- HUD panel shell w/ corner brackets ---------- */
.hud {
    position: relative;
    background: var(--panel);
    border: 1px solid var(--panel-line);
    border-radius: 4px;
    backdrop-filter: blur(6px);
    padding: 10px 14px;
    margin-bottom: 8px;
}
.hud::before, .hud::after {
    content: "";
    position: absolute;
    width: 10px; height: 10px;
    border-color: var(--cyan);
    opacity: 0.85;
}
.hud::before { top: -1px; left: -1px; border-top: 2px solid; border-left: 2px solid; }
.hud::after { bottom: -1px; right: -1px; border-bottom: 2px solid; border-right: 2px solid; }

.hud-label {
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--cyan);
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.hud-label::before { content: "▸"; color: var(--dim); }

/* ---------- top bar ---------- */
.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--panel-line);
    padding: 4px 4px 10px 4px;
    margin-bottom: 10px;
}
.brand {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 20px;
    letter-spacing: 0.06em;
    color: var(--ice);
}
.brand span { color: var(--cyan); }
.sys-status {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: var(--dim);
    display: flex;
    align-items: center;
    gap: 16px;
}
.dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; margin-right: 5px; }
.dot.on { background: var(--green); box-shadow: 0 0 6px var(--green); }
.dot.off { background: var(--dim); }

/* ---------- pipeline trace (horizontal reticle) ---------- */
.trace {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
}
.trace-node {
    flex: 1;
    text-align: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9.5px;
    letter-spacing: 0.06em;
    color: var(--dim);
    text-transform: uppercase;
    padding-top: 8px;
    border-top: 2px solid var(--dim);
    position: relative;
}
.trace-node.done { color: var(--cyan); border-top: 2px solid var(--cyan); }
.trace-node.done::before {
    content: "";
    position: absolute; top: -4px; left: 50%; transform: translateX(-50%);
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--cyan); box-shadow: 0 0 6px var(--cyan);
}

/* ---------- verdict ring ---------- */
.ring-wrap { display: flex; justify-content: center; align-items: center; padding: 6px 0 2px 0; }
.ring {
    width: 118px; height: 118px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    position: relative;
}
.ring-inner {
    width: 96px; height: 96px;
    border-radius: 50%;
    background: var(--void);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center;
}
.ring.approve { background: conic-gradient(var(--green) 0deg 320deg, rgba(57,255,158,0.15) 320deg 360deg); box-shadow: 0 0 22px rgba(57,255,158,0.35); }
.ring.deny { background: conic-gradient(var(--red) 0deg 320deg, rgba(255,59,78,0.15) 320deg 360deg); box-shadow: 0 0 22px rgba(255,59,78,0.35); }
.ring.review { background: conic-gradient(var(--amber) 0deg 320deg, rgba(255,176,32,0.15) 320deg 360deg); box-shadow: 0 0 22px rgba(255,176,32,0.35); }
.ring-verdict {
    font-family: 'Orbitron', sans-serif;
    font-size: 12.5px;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.ring.approve .ring-verdict { color: var(--green); }
.ring.deny .ring-verdict { color: var(--red); }
.ring.review .ring-verdict { color: var(--amber); }
.ring-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 8.5px;
    color: var(--dim);
    margin-top: 2px;
}

/* ---------- scrollable content zones ---------- */
.scrollzone {
    max-height: 132px;
    overflow-y: auto;
    padding-right: 4px;
}
.scrollzone::-webkit-scrollbar { width: 4px; }
.scrollzone::-webkit-scrollbar-thumb { background: var(--panel-line); border-radius: 2px; }

.notes-zone { max-height: 150px; overflow-y: auto; padding-right: 6px; font-size: 13.5px; line-height: 1.45; }
.notes-zone::-webkit-scrollbar { width: 4px; }
.notes-zone::-webkit-scrollbar-thumb { background: var(--panel-line); border-radius: 2px; }

.citation {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11.5px;
    border-left: 2px solid var(--cyan);
    background: rgba(0,229,255,0.05);
    padding: 5px 8px;
    margin-bottom: 5px;
    border-radius: 0 3px 3px 0;
}

/* ---------- gauges ---------- */
.gauge-label {
    display: flex; justify-content: space-between;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    color: var(--dim);
    margin-bottom: 3px;
}
.gauge-track { background: rgba(255,255,255,0.06); border-radius: 3px; height: 6px; overflow: hidden; }
.gauge-fill { height: 100%; border-radius: 3px; }

/* ---------- inputs ---------- */
textarea {
    background: rgba(0,0,0,0.35) !important;
    color: var(--ice) !important;
    border: 1px solid var(--panel-line) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
}
.stButton > button {
    background: var(--cyan) !important;
    color: #04141C !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em;
    border: none !important;
    border-radius: 4px !important;
    width: 100%;
}
.stButton > button:hover { filter: brightness(1.1); box-shadow: 0 0 14px rgba(0,229,255,0.5); }
[data-testid="stTextInput"] input {
    background: rgba(0,0,0,0.35) !important;
    color: var(--ice) !important;
    border: 1px solid var(--panel-line) !important;
    font-family: 'IBM Plex Mono', monospace !important;
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

kb_dot = "on" if kb_ready else "off"
kb_text = f"{kb_count} CHUNKS LOADED" if kb_ready else "KB IDLE"

st.markdown(f"""
<div class="topbar">
    <div class="brand">ADJUDICATO<span>R</span> // CASE HUD</div>
    <div class="sys-status">
        <span><span class="dot {kb_dot}"></span>KNOWLEDGE BASE: {kb_text}</span>
        <span>CASE: {st.session_state.case_number}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# API key -- kept out of the main canvas so the dashboard stays dense
try:
    key_ctx = st.popover("⚙ SYSTEM ACCESS KEY")
except AttributeError:
    key_ctx = st.expander("⚙ SYSTEM ACCESS KEY")

with key_ctx:
    api_key_input = st.text_input(
        "Groq API key",
        type="password",
        help="Get a free key at https://console.groq.com/keys. Kept only in this session."
    )
    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input
    st.caption("Required before filing a claim.")

# =====================================================================
# TRACE HELPERS
# =====================================================================
TRACE_STEPS = [
    ("retrieve", "RETRIEVE"),
    ("grade", "GRADE"),
    ("decision", "DECIDE"),
    ("hallucination", "VERIFY"),
]

def render_trace(done_keys=None):
    done_keys = done_keys or set()
    nodes = ""
    for key, label in TRACE_STEPS:
        cls = "trace-node done" if key in done_keys else "trace-node"
        nodes += f'<div class="{cls}">{label}</div>'
    return f'<div class="trace">{nodes}</div>'

def gauge(label, value):
    pct = max(0, min(100, round(value * 100)))
    color = "var(--green)" if pct >= 70 else ("var(--amber)" if pct >= 40 else "var(--red)")
    st.markdown(f"""
    <div class="gauge-label"><span>{label}</span><span>{value:.2f}</span></div>
    <div class="gauge-track"><div class="gauge-fill" style="width:{pct}%; background:{color};"></div></div>
    """, unsafe_allow_html=True)

# =====================================================================
# MAIN GRID -- everything below fits in one pass, no page-level scroll
# =====================================================================
col_intake, col_verdict, col_evidence = st.columns([1, 1.05, 1], gap="small")

with col_intake:
    st.markdown('<div class="hud" style="min-height:238px;">', unsafe_allow_html=True)
    st.markdown('<div class="hud-label">STATEMENT OF LOSS</div>', unsafe_allow_html=True)
    claim = st.text_area(
        "Statement of loss",
        height=140,
        label_visibility="collapsed",
        placeholder="Describe what happened, when, and what was damaged or lost..."
    )
    submitted = st.button("▶ FILE CLAIM")
    st.markdown("</div>", unsafe_allow_html=True)

trace_slot = col_verdict.empty()
verdict_slot = col_verdict.empty()

with col_evidence:
    rag_slot = st.empty()
    citation_slot = st.empty()

notes_slot = st.empty()

def draw_idle():
    with trace_slot.container():
        st.markdown('<div class="hud">', unsafe_allow_html=True)
        st.markdown('<div class="hud-label">PIPELINE TRACE</div>', unsafe_allow_html=True)
        st.markdown(render_trace(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with verdict_slot.container():
        st.markdown('<div class="hud" style="min-height:130px;">', unsafe_allow_html=True)
        st.markdown('<div class="hud-label">VERDICT</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="ring-wrap">
            <div class="ring" style="background:rgba(79,107,122,0.15); box-shadow:none;">
                <div class="ring-inner"><span class="ring-sub">AWAITING<br>CLAIM</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with rag_slot.container():
        st.markdown('<div class="hud" style="min-height:98px;">', unsafe_allow_html=True)
        st.markdown('<div class="hud-label">RAG QUALITY</div>', unsafe_allow_html=True)
        st.caption("Scores populate after a claim is filed.")
        st.markdown("</div>", unsafe_allow_html=True)

    with citation_slot.container():
        st.markdown('<div class="hud" style="min-height:118px;">', unsafe_allow_html=True)
        st.markdown('<div class="hud-label">POLICY CITATIONS</div>', unsafe_allow_html=True)
        st.markdown('<div class="scrollzone"><span style="color:var(--dim); font-family:\'IBM Plex Mono\',monospace; font-size:11.5px;">No citations yet.</span></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with notes_slot.container():
        st.markdown('<div class="hud">', unsafe_allow_html=True)
        st.markdown('<div class="hud-label">CASE NOTES</div>', unsafe_allow_html=True)
        st.markdown('<div class="notes-zone" style="color:var(--dim);">Reasoning will appear here once the claim is processed.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

if not submitted:
    draw_idle()

if submitted:

    if not os.environ.get("GROQ_API_KEY"):
        st.error("Enter your Groq API key via the ⚙ SYSTEM ACCESS KEY panel before filing a claim.")
        draw_idle()
        st.stop()

    if not claim.strip():
        st.warning("Enter a statement of loss before filing the claim.")
        draw_idle()
        st.stop()

    with trace_slot.container():
        st.markdown('<div class="hud">', unsafe_allow_html=True)
        st.markdown('<div class="hud-label">PIPELINE TRACE — RUNNING</div>', unsafe_allow_html=True)
        st.markdown(render_trace(), unsafe_allow_html=True)
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

        with trace_slot.container():
            st.markdown('<div class="hud">', unsafe_allow_html=True)
            st.markdown('<div class="hud-label">PIPELINE TRACE — COMPLETE</div>', unsafe_allow_html=True)
            st.markdown(render_trace({"retrieve", "grade", "decision", "hallucination"}), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        decision = result.get("decision", "MANUAL_REVIEW")
        reasoning = result.get("reasoning", "No reasoning provided.")
        citations = result.get("citations", [])
        needs_human = result.get("needs_human", False)

        ring_class = {"APPROVE": "approve", "DENY": "deny"}.get(decision, "review")
        ring_label = {"APPROVE": "APPROVED", "DENY": "DENIED"}.get(decision, "MANUAL REVIEW")

        with verdict_slot.container():
            st.markdown('<div class="hud" style="min-height:130px;">', unsafe_allow_html=True)
            st.markdown('<div class="hud-label">VERDICT</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="ring-wrap">
                <div class="ring {ring_class}">
                    <div class="ring-inner">
                        <span class="ring-verdict">{ring_label}</span>
                        <span class="ring-sub">{st.session_state.case_number}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if needs_human:
                st.caption("⚠ Escalated for manual adjuster review.")
            st.markdown("</div>", unsafe_allow_html=True)

        with citation_slot.container():
            st.markdown('<div class="hud" style="min-height:118px;">', unsafe_allow_html=True)
            st.markdown('<div class="hud-label">POLICY CITATIONS</div>', unsafe_allow_html=True)
            st.markdown('<div class="scrollzone">', unsafe_allow_html=True)
            if citations:
                for c in citations:
                    st.markdown(f'<div class="citation">{c}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color:var(--dim); font-family:\'IBM Plex Mono\',monospace; font-size:11.5px;">No specific citations found.</span>', unsafe_allow_html=True)
            st.markdown("</div></div>", unsafe_allow_html=True)

        with notes_slot.container():
            st.markdown('<div class="hud">', unsafe_allow_html=True)
            st.markdown('<div class="hud-label">CASE NOTES</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="notes-zone">{reasoning}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with rag_slot.container():
            st.markdown('<div class="hud" style="min-height:98px;">', unsafe_allow_html=True)
            st.markdown('<div class="hud-label">RAG QUALITY</div>', unsafe_allow_html=True)
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
        st.error(f"Graph returned an incomplete state. Missing key: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
