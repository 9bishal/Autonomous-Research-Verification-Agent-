"""
agents/analyst.py
=================
AGENT 3 — The Analyst

WHAT IT DOES:
  Takes the raw web search results from the Researcher and extracts
  clean, structured insights for each subtask. Removes fluff,
  pulls out facts, numbers, and key findings.

WHY IT EXISTS:
  Raw search results are messy — HTML fragments, repeated text,
  irrelevant content. The Analyst acts as a filter and synthesiser.
  It gives the Writer clean, structured material to work with.

HOW TO EXPLAIN TO HR:
  "The Analyst takes raw scraped content — which is messy and
   unstructured — and extracts 3 to 5 clean, specific insights
   per subtask. It's the difference between handing the Writer a
   stack of unread articles versus a highlighted summary. This
   separation of concerns also means I can swap the Analyst's
   prompt independently without touching any other agent."

Input  → state["raw_research"]
Output → state["structured_insights"]
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AppState

load_dotenv()

# ── LLM setup ─────────────────────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)


def _combine_sources(sources: list[dict]) -> str:
    """
    Combine multiple source contents into one text block for the LLM.
    Limits each source to 600 chars to stay within context limits.
    """
    parts = []
    for s in sources:
        parts.append(f"Source: {s['url']}\n{s['content'][:600]}")
    return "\n\n---\n\n".join(parts)


def _extract_insights_for_subtask(subtask: str, sources: list[dict]) -> str:
    """
    Ask the LLM to extract key insights from the sources for one subtask.
    Returns a formatted string of bullet-point insights.
    """

    combined_content = _combine_sources(sources)

    response = llm.invoke([
        SystemMessage(content="""You are a research analyst.
Extract exactly 3-5 specific, factual insights from the sources below.

Rules:
- Use real numbers and statistics when available
- Be specific — no vague statements like "many companies"
- Each insight must be a single clear sentence
- Return as a numbered list

No preamble. Just the numbered insights."""),

        HumanMessage(content=f"""
Research Question: {subtask}

Sources:
{combined_content}

Extract 3-5 key insights:""")
    ])

    return f"### {subtask}\n{response.content}"


def analyst_agent(state: AppState) -> dict:
    """
    MAIN FUNCTION — called by LangGraph as a node.

    For each subtask, extracts structured insights from raw sources.

    Reads:  state["raw_research"]
    Writes: state["structured_insights"]
    """

    insights = []

    for research_item in state["raw_research"]:
        insight = _extract_insights_for_subtask(
            subtask = research_item["subtask"],
            sources = research_item["sources"],
        )
        insights.append(insight)

    return {"structured_insights": insights}
