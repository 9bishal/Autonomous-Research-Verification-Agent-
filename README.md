# Autonomous Research & Verification Agent

> **5 AI Agents · LangGraph · Human-in-the-Loop · Fact-Checking · FastAPI · Groq LLaMA 3.3 70B**

**GitHub:** https://github.com/9bishal/Autonomous-Research-Verification-Agent-

---

## What it does

Enter any research topic -> 5 specialised agents collaborate to deliver a structured,
fact-checked report with a human approval gate before the report is written.
Download the final report as a **styled PDF**.

```
Topic Input
  |
  v
Orchestrator    ->  Breaks topic into 5 focused research subtasks
  |
  v
Researcher      ->  Parallel Tavily web search (5 queries simultaneously)
  |
  v
Analyst         ->  Extracts 3-5 specific insights per subtask
  |
  v
HUMAN REVIEW    ->  You review insights before the report is written
  |
  v (approved)
Writer          ->  Compiles professional structured markdown report
  |
  v
Fact Checker    ->  Validates every claim: VERIFIED / UNVERIFIED / DISPUTED
  |
  v
Final Report + PDF Download + Fact-Check Score
```

---

## Key Features

| Feature | Why it matters |
|---------|----------------|
| Human-in-the-Loop gate | Pipeline pauses; full state preserved by LangGraph MemorySaver |
| Parallel research | All 5 Tavily searches run simultaneously via ThreadPoolExecutor |
| Fact-Checker agent | Validates every claim - addresses LLM hallucination directly |
| PDF export | Styled PDF download with professional typography |
| FastAPI REST endpoint | Full deployable microservice with /start, /approve, /status |
| Typed shared state | AppState TypedDict - every agent I/O contract is explicit |

---

## Tech Stack

- **LangGraph** - Agent orchestration + HITL interrupt + MemorySaver checkpointing
- **Groq LLaMA 3.3 70B** - Ultra-fast LLM inference for all 5 agents
- **Tavily** - Real-time web search API
- **FastAPI** - Production REST API layer
- **Streamlit** - Interactive UI with 3-phase workflow
- **xhtml2pdf** - Markdown to styled PDF export

---

## Quick Start

```bash
git clone https://github.com/9bishal/Autonomous-Research-Verification-Agent-.git
cd Autonomous-Research-Verification-Agent-
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add GROQ_API_KEY + TAVILY_API_KEY
streamlit run app.py        # launch Streamlit UI
uvicorn api.main:app --reload  # launch FastAPI (separate terminal)
```
