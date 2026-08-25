"""
qa_agent.py
-----------
Powers the "Settlement Q&A agent" feature: answers natural-language
questions about a specific reconciliation run, grounded strictly in that
run's own JSON output. The model is explicitly told not to use outside
knowledge and to say so if the data doesn't contain the answer -- this is
what keeps it from hallucinating a number that was never actually computed.
"""

import json
import os

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a finance ops assistant answering questions about \
ONE specific reconciliation run. You will be given that run's full result \
data as JSON. Answer ONLY using that data -- if the data doesn't contain \
what's needed to answer, say so plainly rather than guessing. Keep answers \
to 2-4 sentences, concrete and specific (cite actual IDs/numbers from the \
data where relevant). No markdown headers, just plain prose."""


def _mock_answer(question: str, result_context: dict) -> str:
    """Deterministic fallback so the Q&A panel works without an API key."""
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
    return "(mock) I can only give simple canned answers without a live API key -- set ANTHROPIC_API_KEY for full reasoning."


def answer_question(question: str, result_context: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return {"answer": _mock_answer(question, result_context), "mode": "mock"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

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

        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Reconciliation run data:\n{json.dumps(trimmed, default=str)}\n\nQuestion: {question}",
            }],
        )
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return {"answer": text.strip(), "mode": "live"}
    except Exception as e:
        return {
            "answer": f"(mock, live call failed: {type(e).__name__}) " + _mock_answer(question, result_context),
            "mode": "mock",
        }
