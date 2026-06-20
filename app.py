"""
app.py
======
Streamlit UI for the Multi-Agent Research & Report System

IMPORTANT — TWO-PHASE UI:
  Phase 1: User enters topic → pipeline runs → pauses at HITL gate
           UI shows the structured insights for review

  Phase 2: User clicks Approve or Reject
           If approved → Writer + Fact-Checker run → final report shown
           If rejected → session ends
"""

import uuid
import streamlit as st
import plotly.graph_objects as go

from graph.workflow import research_graph

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Research System",
    page_icon="🔬",
    layout="wide",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id"  not in st.session_state: st.session_state.session_id  = str(uuid.uuid4())
if "phase"       not in st.session_state: st.session_state.phase       = "input"   # input | review | complete
if "graph_state" not in st.session_state: st.session_state.graph_state = None

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔬 Multi-Agent Research & Report System")
st.caption("**LangGraph** · **5 AI Agents** · **Human-in-the-Loop** · **Fact-Checking** · **FastAPI** · **Groq LLaMA 3.3 70B**")

# ── Pipeline diagram ──────────────────────────────────────────────────────────
with st.expander("📊 Agent Pipeline Architecture", expanded=False):
    st.markdown("""
```
Topic Input
    │
    ▼
🎯 Orchestrator    →  Breaks topic into 5 focused research subtasks
    │
    ▼
🔍 Researcher      →  Parallel Tavily searches (5 searches simultaneously)
    │
    ▼
🧠 Analyst         →  Extracts 3-5 specific insights per subtask
    │
    ▼
⏸  HUMAN REVIEW   →  YOU review insights — Approve or Reject
    │
    ▼ (approved)
✍️  Writer          →  Compiles professional structured report
    │
    ▼
✅  Fact Checker   →  Validates every claim → VERIFIED / UNVERIFIED / DISPUTED
    │
    ▼
📄  Final Report
```
**All agents share one AppState object — LangGraph manages state seamlessly.**
    """)

st.divider()

config = {"configurable": {"thread_id": st.session_state.session_id}}


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — INPUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "input":

    st.subheader("🎯 Enter Research Topic")
    topic = st.text_input(
        "What do you want to research?",
        placeholder="e.g.  Impact of Generative AI on software engineering jobs in India 2025",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        run = st.button("🚀 Start Research", type="primary", disabled=not topic.strip())
    with col2:
        st.caption("The pipeline runs Orchestrator → Researcher → Analyst, then pauses for your review.")

    if run and topic.strip():
        node_labels = {
            "orchestrator": ("🎯", "Orchestrator",  "Breaking topic into research subtasks..."),
            "researcher":   ("🔍", "Researcher",    "Searching web in parallel (5 queries)..."),
            "analyst":      ("🧠", "Analyst",       "Extracting structured insights..."),
        }

        # Status cards
        cols = st.columns(3)
        slots = {}
        for i, (k, (icon, label, _)) in enumerate(node_labels.items()):
            slots[k] = cols[i].empty()
            slots[k].info(f"{icon} **{label}**\n\nWaiting...")

        with st.status("Running research pipeline...", expanded=True) as status:
            for event in research_graph.stream(
                {"topic": topic.strip()},
                config=config,
            ):
                node = list(event.keys())[0]
                if node in node_labels:
                    icon, label, desc = node_labels[node]
                    st.write(f"{icon} **{label}** — {desc}")
                    slots[node].success(f"{icon} **{label}**\n\n✅ Done")

            status.update(
                label="⏸ Pipeline paused — waiting for your review",
                state="complete"
            )

        st.session_state.graph_state = research_graph.get_state(config).values
        st.session_state.phase = "review"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — HUMAN REVIEW (HITL GATE)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "review":

    s = st.session_state.graph_state

    st.subheader("⏸ Human Review Gate")
    st.info("The pipeline has paused. Review the research insights below before the report is written.")

    # Show research plan
    with st.expander("📋 Research Plan (Orchestrator output)", expanded=False):
        for i, task in enumerate(s.get("subtasks", []), 1):
            st.markdown(f"**{i}.** {task}")

    # Show insights
    st.subheader("🧠 Analyst Insights — Review Before Approving")
    insights = s.get("structured_insights", [])
    for insight in insights:
        st.markdown(insight)
        st.divider()

    # Optional feedback
    feedback = st.text_area(
        "📝 Optional feedback for the Writer (leave blank to proceed as-is)",
        placeholder="e.g. Focus more on India-specific data. Add a section on salary trends.",
        height=80,
    )

    # Approve / Reject buttons
    st.markdown("**Your decision:**")
    col_approve, col_reject, _ = st.columns([1, 1, 3])

    with col_approve:
        if st.button("✅ Approve — Generate Report", type="primary"):
            with st.status("Generating report + fact-checking...", expanded=True) as status:

                node_labels = {
                    "human_review": ("⏸", "Human Review",  "Processing approval..."),
                    "writer":       ("✍️", "Writer",        "Writing structured report..."),
                    "fact_checker": ("✅", "Fact Checker",  "Validating every claim..."),
                }
                cols2 = st.columns(3)
                slots2 = {}
                for i, (k, (icon, label, _)) in enumerate(node_labels.items()):
                    slots2[k] = cols2[i].empty()
                    slots2[k].info(f"{icon} **{label}**\n\nWaiting...")

                for event in research_graph.stream(
                    {
                        "human_approved": True,
                        "human_feedback": feedback.strip(),
                    },
                    config=config,
                ):
                    node = list(event.keys())[0]
                    if node in node_labels:
                        icon, label, desc = node_labels[node]
                        st.write(f"{icon} **{label}** — {desc}")
                        slots2[node].success(f"{icon} **{label}**\n\n✅ Done")

                status.update(label="✅ Report complete!", state="complete")

            st.session_state.graph_state = research_graph.get_state(config).values
            st.session_state.phase = "complete"
            st.rerun()

    with col_reject:
        if st.button("❌ Reject — Start Over"):
            st.session_state.phase       = "input"
            st.session_state.session_id  = str(uuid.uuid4())
            st.session_state.graph_state = None
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — COMPLETE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "complete":

    s = st.session_state.graph_state

    verified = s.get("facts_verified", 0)
    disputed = s.get("facts_disputed", 0)
    total    = len(s.get("fact_check_results", []))
    score    = round((verified / total) * 100) if total > 0 else 0

    # Top metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Research Subtasks",  len(s.get("subtasks", [])))
    c2.metric("Sources Consulted",  len(s.get("subtasks", [])) * 3)
    c3.metric("Facts Verified",     f"{verified} / {total}")
    c4.metric("Fact-Check Score",   f"{score}%",
              delta="✅ Verified" if score >= 70 else "⚠️ Review needed")

    st.divider()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📄 Final Report", "✅ Fact-Check Details", "🔍 Research Plan"])

    with tab1:
        st.markdown(s.get("final_report", ""))
        st.download_button(
            "📥 Download Report (.md)",
            data      = s.get("final_report", ""),
            file_name = "research_report.md",
            mime      = "text/markdown",
        )

    with tab2:
        results = s.get("fact_check_results", [])
        if results:
            for r in results:
                icon = "✅" if r["verdict"] == "VERIFIED" else "❓" if r["verdict"] == "UNVERIFIED" else "❌"
                with st.expander(f"{icon} {r['verdict']} — {r['claim'][:80]}"):
                    st.caption(f"Source: {r['source']}")

            # Pie chart
            counts = {
                "VERIFIED":   sum(1 for r in results if r["verdict"] == "VERIFIED"),
                "UNVERIFIED": sum(1 for r in results if r["verdict"] == "UNVERIFIED"),
                "DISPUTED":   sum(1 for r in results if r["verdict"] == "DISPUTED"),
            }
            fig = go.Figure(go.Pie(
                labels = list(counts.keys()),
                values = list(counts.values()),
                marker_colors = ["#10B981", "#F59E0B", "#EF4444"],
            ))
            fig.update_layout(title="Claim Verification Breakdown", height=350,
                              paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        for i, task in enumerate(s.get("subtasks", []), 1):
            st.markdown(f"**{i}.** {task}")

    st.divider()
    if st.button("🔄 New Research"):
        st.session_state.phase       = "input"
        st.session_state.session_id  = str(uuid.uuid4())
        st.session_state.graph_state = None
        st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔬 About")
    st.markdown("""
**5 Agents:**
1. 🎯 Orchestrator — research plan
2. 🔍 Researcher — parallel web search
3. 🧠 Analyst — structured insights
4. ✍️ Writer — professional report
5. ✅ Fact Checker — claim validation

**Key Features:**
- Human-in-the-Loop gate
- Parallel search (5× faster)
- LLM hallucination detection
- FastAPI REST endpoint
- LangGraph state machine
    """)
    phase_labels = {"input": "📝 Awaiting input", "review": "⏸ Awaiting review", "complete": "✅ Complete"}
    st.info(f"**Status:** {phase_labels.get(st.session_state.phase, '—')}")
