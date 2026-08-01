import os
import uuid

import streamlit as st
from graph import graph

st.set_page_config(
    page_title="VerdynenAI",
    page_icon="📁",
    layout="wide",  # Changed to wide layout to eliminate scrolling
    initial_sidebar_state="collapsed",
)

# =====================================================================
# PREMIUM UX / UI DESIGN TOKENS & ANIMATIONS
# =====================================================================
st.markdown("""
<style>

/* ============================
   THEME VARIABLES
============================ */

:root {
    --ink: #14161A;
    --muted: #6B7280;
    --border: #E5E7EB;
    --surface: #FFFFFF;
    --canvas: #FAFAFA;
    --accent: #4F46E5;
    --accent-soft: #EEF2FF;
}

/* ============================
   PAGE
============================ */

.stApp {
    background: var(--canvas);
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, p, span, div, label {
    color: var(--ink);
}

.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1400px !important;
}

#MainMenu,
footer,
header {
    visibility: hidden;
}

/* ============================
   INPUTS
============================ */

textarea,
input {
    background: var(--surface) !important;
    color: var(--ink) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* Fix placeholder text */

textarea::placeholder,
input::placeholder {
    color: #9CA3AF !important;
}

/* Streamlit text input */

.stTextInput input {
    background: white !important;
    color: black !important;
}

.stTextArea textarea {
    background: white !important;
    color: black !important;
}

/* ============================
   BUTTONS
============================ */

.stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    height: 40px !important;
    width: 100% !important;
}

.stButton > button:hover {
    background: #4338CA !important;
}

/* ============================
   POPOVER BUTTON
============================ */

[data-testid="stPopover"] button {
    background: white !important;
    color: black !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    min-height: 42px !important;
}

[data-testid="stPopover"] button span,
[data-testid="stPopover"] button p,
[data-testid="stPopover"] button div {
    color: black !important;
}

/* Hover */

[data-testid="stPopover"] button:hover {
    background: #F3F4F6 !important;
}

/* ============================
   POPOVER CONTENT
============================ */

[data-testid="stPopoverContent"] {
    background: white !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 12px !important;
}

[data-testid="stPopoverContent"] * {
    color: black !important;
}

/* ============================
   PASSWORD FIELD INSIDE POPOVER
============================ */

[data-testid="stPopoverContent"] input {
    background: white !important;
    color: black !important;
    border: 1px solid #D1D5DB !important;
}

/* ============================
   DARK THEME SUPPORT
============================ */

@media (prefers-color-scheme: dark) {

    [data-testid="stPopover"] button {
        background: #1F2937 !important;
        color: white !important;
        border: 1px solid #374151 !important;
    }

    [data-testid="stPopover"] button * {
        color: white !important;
    }

    [data-testid="stPopoverContent"] {
        background: #111827 !important;
    }

    [data-testid="stPopoverContent"] * {
        color: white !important;
    }

    [data-testid="stPopoverContent"] input {
        background: #1F2937 !important;
        color: white !important;
        border: 1px solid #374151 !important;
    }
}

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
        <div class="page-title">VerdynenAI_Claims Adjudicator</div>
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
