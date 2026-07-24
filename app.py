import os
import uuid

import streamlit as st
from graph import graph

st.set_page_config(
    page_title="Claims Adjudicator",
    page_icon="🛡️",
    layout="wide",  # Changed to wide layout to eliminate scrolling
    initial_sidebar_state="collapsed",
)

# =====================================================================
# PREMIUM UX / UI DESIGN TOKENS & ANIMATIONS
# =====================================================================
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
    padding: 1.5rem 2rem !important;
    max-width: 1400px !important;
}
.stApp { background: var(--canvas); font-family: 'Inter', sans-serif; }
h1,h2,h3,p,span,div,label { color: var(--ink); }

/* ---------- top bar ---------- */
.top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
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

/* ---------- sleek dashboard cards ---------- */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 2px rgba(20,22,26,0.02);
}
.eyebrow {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
}
.hint {
    font-size: 14px;
    color: var(--muted);
    font-style: italic;
    text-align: center;
    padding: 40px 0;
}

/* ---------- animated pipeline timeline ---------- */
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-6px); }
    to { opacity: 1; transform: translateX(0); }
}
.tl-row {
    display: flex; align-items: center; gap: 10px;
    font-size: 13.5px;
    padding: 6px 0;
    animation: slideIn 0.25s ease-out forwards;
}
.tl-check {
    width: 18px; height: 18px; border-radius: 50%;
    background: var(--accent-soft); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; flex-shrink: 0;
}

/* ---------- verdict banner ---------- */
@keyframes popUp {
    from { opacity: 0; transform: scale(0.98); }
    to { opacity: 1; transform: scale(1); }
}
.verdict {
    display: flex; align-items: center; gap: 14px;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
    animation: popUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.verdict.approve { background: #ECFDF3; border: 1px solid #86EFAC; }
.verdict.deny { background: #FEF2F2; border: 1px solid #FCA5A5; }
.verdict.review { background: #FFFBEB; border: 1px solid #FDE68A; }
.verdict-icon { font-size: 24px; line-height: 1; }
.verdict-word { font-size: 19px; font-weight: 700; letter-spacing: -0.01em; }
.verdict.approve .verdict-word { color: #15803D; }
.verdict.deny .verdict-word { color: #B91C1C; }
.verdict.review .verdict-word { color: #B45309; }
.verdict-case { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--muted); margin-top: 1px; }

/* ---------- reasoning panel (scroll protected) ---------- */
.reasoning {
    font-size: 14.5px;
    line-height: 1.6;
    color: var(--ink);
    max-height: 200px;
    overflow-y: auto;
    padding-right: 4px;
}
.reasoning::-webkit-scrollbar { width: 4px; }
.reasoning::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ---------- citation chips ---------- */
.citation-chip {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    background: var(--accent-soft);
    color: var(--accent);
    border-radius: 6px;
    padding: 4px 8px;
    margin: 0 6px 6px 0;
}

/* ---------- metrics gauge grid ---------- */
.stat-grid { display: flex; gap: 12px; width: 100%; }
.stat-card {
    flex: 1;
    background: var(--canvas);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
}
.stat-label { font-size: 11px; color: var(--muted); margin-bottom: 2px; }
.stat-value { font-size: 24px; font-weight: 700; }
.stat-track { background: var(--border); border-radius: 2px; height: 4px; overflow: hidden; margin-top: 6px; }
.stat-fill { height: 100%; border-radius: 2px; transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1); }

/* ---------- st framework cleanups ---------- */
textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 14.5px !important;
    color: var(--ink) !important;
}
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: 14.5px !important;
    border: none !important;
    border-radius: 8px !important;
    height: 40px !important;
    width: 100% !important;
}
.stButton > button:hover { background: #4338CA !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# PERSISTENT SESSION STATE SETUP
# =====================================================================
if "case_number" not in st.session_state:
    st.session_state.case_number = "CF-" + str(uuid.uuid4())[:8].upper()

# =====================================================================
# GLOBAL TOP DASHBOARD NAVBAR
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
        <div class="page-sub">AI-assisted policy claim evaluation workspace</div>
    </div>
    <div class="meta">
        <div class="kb-chip"><span class="kb-dot {kb_dot}"></span>{kb_label}</div>
        <div class="kb-chip">{st.session_state.case_number}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# TWO-COLUMN COMPACT LAYOUT ENGINE (PREVENTS SCROLLING)
# =====================================================================
left_col, right_col = st.columns([4, 5], gap="large")

with left_col:
    # 1. API Configuration Context Panel
    try:
        key_ctx = st.popover("⚙ Configure Workspace Credentials", use_container_width=True)
    except AttributeError:
        key_ctx = st.expander("⚙ Configure Workspace Credentials")

    with key_ctx:
        api_key_input = st.text_input(
            "Groq API Key",
            type="password",
            help="Get your key at https://console.groq.com/keys"
        )
        if api_key_input:
            os.environ["GROQ_API_KEY"] = api_key_input

    # 2. Main Process Submission Card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Statement of Loss Input</div>', unsafe_allow_html=True)
    claim = st.text_area(
        "Statement of loss",
        height=140,
        label_visibility="collapsed",
        placeholder="Provide a chronological description of what happened, transaction records, damage reports, or itemizations..."
    )
    submitted = st.button("Analyze & File Claim")
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. Dynamic Pipeline Progress View Frame
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Active Pipeline Diagnostics</div>', unsafe_allow_html=True)
    timeline_slot = st.empty()
    timeline_slot.markdown('<p style="color:var(--muted); font-size:13px; margin:0;">Awaiting pipeline initiation...</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


NODE_LABELS = {
    "retrieve": "Retrieving context matching loss profile",
    "grade": "Validating document relevance parameters",
    "rewrite": "Optimizing semantic search metrics",
    "web": "Sourcing external environmental conditions",
    "decision": "Generating automated decision logic",
    "hallucination": "Cross-verifying source grounds",
    "human": "Flagging data for senior validation",
    "finish": "Compiling final case diagnostic payload",
}

def render_timeline(steps):
    rows = ""
    for key in steps:
        label = NODE_LABELS.get(key, key)
        rows += f'<div class="tl-row"><span class="tl-check">✓</span>{label}</div>'
    return rows

def gauge_card(label, value):
    pct = max(0, min(100, round(value * 100)))
    color = "#15803D" if pct >= 70 else ("#B45309" if pct >= 40 else "#B91C1C")
    return f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">{value:.2f}</div><div class="stat-track"><div class="stat-fill" style="width:{pct}%; background:{color};"></div></div></div>'


# =====================================================================
# EVALUATION & STREAM PROCESSING EXECUTION ENGINE
# =====================================================================
with right_col:
    if not submitted:
        st.markdown('<div class="card" style="height: 100%; min-height: 450px; display: flex; align-items: center; justify-content: center;"><p class="hint">Adjudicator output payload, evaluation logs, and RAG tracking metrics will render here in real-time once analysis begins.</p></div>', unsafe_allow_html=True)

    else:
        # Front-end guard rails
        if not os.environ.get("GROQ_API_KEY"):
            st.error("Missing Workspace Credentials. Provide your Groq API key to activate execution vectors.")
            st.stop()

        if not claim.strip():
            st.warning("The loss payload statement is blank. Provide description input prior to execution.")
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
        
        completed_steps = []
        accumulated_state = dict(initial_state)

        # Unified Native User Spinner & Processor Animation overlay
        with st.spinner("Processing agent networks and verifying metrics..."):
            try:
                for step_output in graph.stream(initial_state, config=config):
                    for node_name, node_state in step_output.items():
                        if isinstance(node_state, dict):
                            accumulated_state.update(node_state)
                        completed_steps.append(node_name)
                        
                        # Fluidly animate step progression into the left column layout slot
                        timeline_slot.markdown(render_timeline(completed_steps), unsafe_allow_html=True)

                result = accumulated_state
                decision = result.get("decision", "MANUAL_REVIEW")
                reasoning = result.get("reasoning", "No technical logs generated.")
                citations = result.get("citations", [])
                needs_human = result.get("needs_human", False)

                verdict_class = {"APPROVE": "approve", "DENY": "deny"}.get(decision, "review")
                verdict_icon = {"APPROVE": "✅", "DENY": "⛔"}.get(decision, "🔎")
                verdict_word = {"APPROVE": "Approved", "DENY": "Denied"}.get(decision, "Manual Review")

                # 1. Output Target: Case Decision Banner
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
                    st.warning("Operational escalation triggered: Case routing to senior adjuster desk.")

                # 2. Output Target: Case Reasoning Logs
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="eyebrow">Technical Evaluation Notes</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="reasoning">{reasoning}</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # 3. Output Target: Citations
                if citations:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div class="eyebrow">Documented Policy References</div>', unsafe_allow_html=True)
                    chips = "".join(f'<span class="citation-chip">{c}</span>' for c in citations)
                    st.markdown(chips, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                # 4. Output Target: Clean RAG Quality Gauge Array (Zero Layout Glitches)
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="eyebrow">RAG Network Health Metrics</div>', unsafe_allow_html=True)
                try:
                    from ragas_eval import evaluate_claim_result
                    scores = evaluate_claim_result(claim, result)
                    
                    card_1 = gauge_card("Faithfulness Grounding", scores.get("faithfulness", 0))
                    card_2 = gauge_card("Contextual Relevancy", scores.get("answer_relevancy", 0))
                    
                    st.markdown(f'<div class="stat-grid">{card_1}{card_2}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.caption(f"Scoring payload evaluation interrupted: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

            except KeyError as e:
                st.error(f"Incomplete structural layout processing. Missing key: {e}")
            except Exception as e:
                st.error(f"System-level exception encountered: {e}")
