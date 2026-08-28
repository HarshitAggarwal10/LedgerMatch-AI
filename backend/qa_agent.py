"""
qa_agent.py
-----------
Powers the "Settlement Q&A agent" feature: answers natural-language
questions about a specific reconciliation run, grounded strictly in that
run's own JSON output. The model is explicitly told not to use outside
knowledge and to say so if the data doesn't contain the answer -- this is
what keeps it from hallucinating a number that was never actually computed.

Provider order: Groq -> Claude -> mock (see llm_provider.py).
"""

import json

from llm_provider import call_llm

SYSTEM_PROMPT = """You are a finance ops assistant answering questions about \
ONE specific reconciliation run. You will be given that run's full result \
data as JSON. Answer ONLY using that data -- if the data doesn't contain \
what's needed to answer, say so plainly rather than guessing. Keep answers \
to 2-4 sentences, concrete and specific (cite actual IDs/numbers from the \
data where relevant). No markdown headers, just plain prose."""


def _mock_answer(question: str, result_context: dict) -> str:
    """Deterministic fallback so the Q&A panel works without any API key."""
    q = question.lower()
    scoring = result_context.get("scoring") or {}
    exceptions = result_context.get("exceptions", [])

    if "unreconciled" in q or "how much" in q:
        total_exception_amount = sum(e.get("amount") or 0 for e in exceptions)
        return (
            f"(mock) There are {len(exceptions)} unresolved exceptions totalling "
            f"roughly Rs.{total_exception_amount:,.2f} in amount across them. "
            f"Match rate for this run was {scoring.get('match_rate_pct', 'unknown')}%."
        )
    if "summar" in q:
        return (
            f"(mock) This run matched {scoring.get('correct_matches', '?')} records "
            f"correctly ({scoring.get('match_rate_pct', '?')}% match rate), with "
            f"{scoring.get('false_match_rate_pct', '?')}% of matches wrong and "
            f"{len(exceptions)} exceptions left for manual review."
        )
    if "worth checking" in q or "priorit" in q:
        top = exceptions[:3]
        ids = ", ".join(e.get("id", "?") for e in top)
        return f"(mock) I'd start with: {ids or 'no exceptions to review'}."
    return "(mock) No live provider is configured -- set GROQ_API_KEY (free tier) or ANTHROPIC_API_KEY in .env for full reasoning."


def answer_question(question: str, result_context: dict) -> dict:
    # Trim the context so we're not shipping huge payloads on every question --
    # the scoring summary + exceptions + a sample of matches is enough signal.
    trimmed = {
        "scoring": result_context.get("scoring"),
        "performance": result_context.get("performance"),
        "exceptions": result_context.get("exceptions", [])[:40],
        "sample_matches": (
            result_context.get("exact_matches", [])[:5]
            + result_context.get("fuzzy_matches", [])[:5]
            + result_context.get("llm_matches", [])[:5]
        ),
        "gateway_reconciliation_summary": {
            k: len(v) for k, v in (result_context.get("gateway_reconciliation") or {}).items()
        },
    }
    user_prompt = f"Reconciliation run data:\n{json.dumps(trimmed, default=str)}\n\nQuestion: {question}"

    result = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=300)

    if result["text"] is not None:
        return {"answer": result["text"], "mode": "live", "provider": result["provider"]}

    prefix = f"(mock, live call failed -- {result['error']}) " if result.get("error") and "no GROQ_API_KEY" not in result["error"] else "(mock) "
    return {"answer": prefix + _mock_answer(question, result_context), "mode": "mock", "provider": None}
