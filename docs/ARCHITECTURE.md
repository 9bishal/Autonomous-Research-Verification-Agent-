# Architecture

## Graph Structure

```python
graph = StateGraph(AppState)

graph.add_node("orchestrator",  orchestrator_agent)
graph.add_node("researcher",    researcher_agent)
graph.add_node("analyst",       analyst_agent)
graph.add_node("human_review",  human_review_node)
graph.add_node("writer",        writer_agent)
graph.add_node("fact_checker",  fact_checker_agent)

graph.set_entry_point("orchestrator")

graph.add_edge("orchestrator", "researcher")
graph.add_edge("researcher",   "analyst")
graph.add_edge("analyst",      "human_review")      # PAUSES before this

graph.add_conditional_edges(
    "human_review",
    _should_continue_after_review,
    {"approved": "writer", "rejected": END}
)

graph.add_edge("writer",       "fact_checker")
graph.add_edge("fact_checker", END)

graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["human_review"],
)
```

---

## How the HITL Interrupt Works

```
graph.invoke({"topic": "..."}, config)
  │
  Orchestrator runs ✅
  Researcher runs   ✅
  Analyst runs      ✅
  │
  ⏸ interrupt_before=["human_review"] fires
  │
  graph.invoke() RETURNS — pipeline is paused
  Full AppState is saved by MemorySaver

[ Streamlit shows insights to user ]
[ User clicks Approve ]

graph.invoke({"human_approved": True}, config)  ← same config/thread_id
  │
  human_review runs ✅
  Conditional edge: approved → writer
  Writer runs       ✅
  Fact Checker runs ✅
  │
  END
```

The key: using the SAME `thread_id` in config both times.
LangGraph finds the saved checkpoint and resumes from it.

---

## Parallel Research (ThreadPoolExecutor)

```python
with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_subtask = {
        executor.submit(_search_one_subtask, subtask): subtask
        for subtask in subtasks
    }
    for future in as_completed(future_to_subtask):
        results.append(future.result())
```

Each subtask search runs in its own thread simultaneously.
as_completed() yields futures as they finish — no blocking.

---

## Fact-Checker Flow

```
draft_report
    │
    ▼
Extract claims  (LLM call 1)
    │
    ▼
For each claim:
    Verify against sources  (LLM call per claim)
    → VERIFIED / UNVERIFIED / DISPUTED
    │
    ▼
Append fact-check table to report
Compute fact-check score = verified / total × 100
```

---

## FastAPI Architecture

```
Client
  │
  POST /research/start   →  invoke graph → pauses at HITL → return session_id + insights
  │
  POST /research/approve →  resume graph with human_approved=True/False → return final report
  │
  GET  /research/{id}    →  read current state → return status + outputs
```

All sessions are isolated by `thread_id` in LangGraph MemorySaver.
