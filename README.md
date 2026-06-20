# 🔬 Multi-Agent Research & Report System

> **5 specialised AI agents · Human-in-the-Loop · Fact-Checking · FastAPI · LangGraph**

**Live Demo:** [your-app.streamlit.app](#) ← update after deploy
**API Docs:**  [your-api.render.com/docs](#) ← update after deploy

---

## What it does

Enter any research topic → 5 agents collaborate to deliver a structured,
fact-checked report — with a human approval gate before the report is written.

```
Topic
  │
  ▼
🎯 Orchestrator    →  Breaks topic into 5 focused research subtasks
  │
  ▼
🔍 Researcher      →  Parallel Tavily web search (5 queries simultaneously)
  │
  ▼
🧠 Analyst         →  Extracts 3-5 specific insights per subtask
  │
  ▼
⏸  HUMAN REVIEW   →  You review insights before the report is written
  │
  ▼
✍️  Writer          →  Compiles professional structured markdown report
  │
  ▼
✅  Fact Checker   →  Validates every claim: VERIFIED / UNVERIFIED / DISPUTED
  │
  ▼
📄  Final Report + Fact-Check Score
```

---

## Key Features

| Feature | Why it's impressive |
|---------|---------------------|
| **Human-in-the-Loop gate** | Pipeline pauses; state preserved by LangGraph MemorySaver |
| **Parallel research** | All 5 Tavily searches run simultaneously via ThreadPoolExecutor |
| **Fact-Checker agent** | Validates every claim — addresses LLM hallucination directly |
| **FastAPI REST endpoint** | Full deployable microservice, not just a demo |
| **Typed shared state** | `AppState` TypedDict — every agent's I/O is explicit |
| **Conditional edges** | Approved → Writer; Rejected → END |

---

## File Structure

```
research-report-system/
├── agents/
│   ├── orchestrator.py     ← Agent 1: breaks topic into subtasks
│   ├── researcher.py       ← Agent 2: parallel Tavily web search
│   ├── analyst.py          ← Agent 3: extracts structured insights
│   ├── human_review.py     ← HITL gate node
│   ├── writer.py           ← Agent 4: compiles the report
│   └── fact_checker.py     ← Agent 5: validates every claim
├── graph/
│   ├── state.py            ← AppState TypedDict
│   └── workflow.py         ← LangGraph StateGraph + interrupt_before
├── api/
│   └── main.py             ← FastAPI with 3 endpoints
├── docs/
│   ├── ARCHITECTURE.md
│   ├── HOW_TO_EXPLAIN.md
│   └── SETUP.md
├── app.py                  ← Streamlit UI (3 phases)
└── test_run.py             ← Terminal test
```

---

## Quick Start

```bash
git clone https://github.com/yourusername/research-report-system
cd research-report-system
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add GROQ_API_KEY + TAVILY_API_KEY
python test_run.py          # test in terminal
streamlit run app.py        # launch Streamlit UI
uvicorn api.main:app --reload  # launch FastAPI (separate terminal)
```
