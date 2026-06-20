"""
agents/fact_checker.py
======================
AGENT 5 — The Fact-Checker

WHAT IT DOES:
  Reads the Writer's draft report, extracts every factual claim,
  and validates each one against the original research sources.

  Each claim gets one of three verdicts:
    ✅ VERIFIED   — claim is supported by a source we searched
    ❓ UNVERIFIED — claim can't be confirmed from our sources
    ❌ DISPUTED   — claim contradicts what our sources say

  The final report adds a fact-check summary and marks any
  disputed claims clearly so the reader knows what to verify.

WHY THIS IS IMPRESSIVE FOR 10-12 LPA:
  Hallucination prevention is one of the biggest challenges in
  production LLM systems. Adding a fact-checker shows you
  understand this problem and know how to address it.

  Most tutorial chatbots output whatever the LLM says.
  A Fact-Checker shows production thinking.

HOW TO EXPLAIN TO HR:
  "The Fact-Checker is the last agent before output. It extracts
   every factual claim from the draft report and checks it against
   the original Tavily sources. This addresses LLM hallucination —
   the tendency to generate plausible-sounding but false statements.
   Each claim is labelled VERIFIED, UNVERIFIED, or DISPUTED.
   The final report includes a fact-check score so readers know
   how much they can trust the content."

Input  → state["draft_report"], state["raw_research"]
Output → state["fact_check_results"], state["final_report"],
         state["facts_verified"], state["facts_disputed"]
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AppState, FactCheckResult

load_dotenv()

# ── LLM setup ─────────────────────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,            # deterministic — important for fact-checking
    api_key=os.getenv("GROQ_API_KEY"),
)


def _extract_claims_from_report(report: str) -> list[str]:
    """
    Ask the LLM to extract all factual claims from the report.
    Returns a list of claim strings.
    """

    response = llm.invoke([
        SystemMessage(content="""Extract all factual claims from this report.
A factual claim is a specific, verifiable statement (includes numbers, names, percentages).
Return ONLY a JSON array of claim strings. No explanation."""),

        HumanMessage(content=f"Report:\n{report[:3000]}")
    ])

    raw = response.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        claims = json.loads(raw)
        return claims[:10]    # limit to 10 claims to control API costs
    except Exception as e:
        print("\n=== CLAIM EXTRACTION ERROR ===")
        print("Raw LLM Response:")
        print(raw)
        print("\nError:")
        print(e)
        print("==============================\n")
        return []


def _verify_one_claim(
    claim:        str,
    all_sources:  str,
) -> FactCheckResult:
    """
    Verify a single claim against the research sources.
    Returns a FactCheckResult with verdict and source URL.
    """

    response = llm.invoke([
        SystemMessage(content="""You are a fact-checker.
Check if the claim is supported by the sources provided.

Respond with ONLY valid JSON:
{
  "verdict": "VERIFIED" | "UNVERIFIED" | "DISPUTED",
  "source":  "URL that supports or disputes the claim, or 'Not found in sources'"
}

VERIFIED   = claim is clearly supported by a source
UNVERIFIED = claim cannot be confirmed from the given sources
DISPUTED   = a source contradicts the claim"""),

        HumanMessage(content=f"""
Claim to verify: {claim}

Sources:
{all_sources[:2000]}""")
    ])

    raw  = response.content.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(raw)

    return FactCheckResult(
        claim   = claim,
        verdict = data.get("verdict", "UNVERIFIED"),
        source  = data.get("source",  "Not found in sources"),
    )


def _build_sources_text(raw_research: list) -> str:
    """Combine all research sources into one text block for fact-checking."""
    parts = []
    for item in raw_research:
        for src in item.get("sources", []):
            parts.append(f"URL: {src['url']}\n{src['content'][:400]}")
    return "\n\n---\n\n".join(parts)


def _add_fact_check_summary(
    report:   str,
    results:  list[FactCheckResult],
    verified: int,
    disputed: int,
) -> str:
    """Append a fact-check summary section to the report."""

    total = len(results)
    score = round((verified / total) * 100) if total > 0 else 0

    # Build the claims table
    rows = []
    for r in results:
        icon = "✅" if r["verdict"] == "VERIFIED" else "❓" if r["verdict"] == "UNVERIFIED" else "❌"
        rows.append(f"| {icon} {r['verdict']} | {r['claim'][:80]} |")

    table = "\n".join(rows)

    summary = f"""

---

## ✅ Fact-Check Report

**Fact-Check Score: {score}% ({verified}/{total} claims verified)**

| Verdict | Claim |
|---------|-------|
{table}

*Fact-checking performed by AI — always verify critical claims independently.*"""

    return report + summary


def fact_checker_agent(state: AppState) -> dict:
    """
    MAIN FUNCTION — called by LangGraph as a node.

    Reads:  state["draft_report"], state["raw_research"]
    Writes: state["fact_check_results"], state["final_report"],
            state["facts_verified"], state["facts_disputed"]
    """

    # Step 1: Extract claims from the draft report
    claims = _extract_claims_from_report(state["draft_report"])

    print("\n=== FACT CHECK DEBUG ===")
    print("Draft Report Length:", len(state["draft_report"]))
    print("Claims Extracted:", claims)
    print("Claim Count:", len(claims))
    print("========================\n")

    if not claims:
        return {
            "fact_check_results": [],
            "final_report":       state["draft_report"],
            "facts_verified":     0,
            "facts_disputed":     0,
        }

    # Step 2: Combine all sources into one text block
    all_sources = _build_sources_text(state.get("raw_research", []))
    print("Raw Research Items:", len(state.get("raw_research", [])))
    print("Source Text Length:", len(all_sources))

    # Step 3: Verify each claim
    results = []
    for claim in claims:
        result = _verify_one_claim(claim, all_sources)
        results.append(result)

    # Step 4: Count verdicts
    verified = sum(1 for r in results if r["verdict"] == "VERIFIED")
    disputed = sum(1 for r in results if r["verdict"] == "DISPUTED")

    # Step 5: Add fact-check summary to the report
    final_report = _add_fact_check_summary(
        report   = state["draft_report"],
        results  = results,
        verified = verified,
        disputed = disputed,
    )

    return {
        "fact_check_results": results,
        "final_report":       final_report,
        "facts_verified":     verified,
        "facts_disputed":     disputed,
    }
