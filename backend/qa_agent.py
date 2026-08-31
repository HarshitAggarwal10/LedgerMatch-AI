
import json
import re

from llm_provider import call_llm

SYSTEM_PROMPT = """You are a finance ops assistant answering questions about \
ONE specific reconciliation run. You will be given that run's full result \
data as JSON. Answer ONLY using that data -- if the data doesn't contain \
what's needed to answer, say so plainly rather than guessing. Keep answers \
to 2-4 sentences, concrete and specific (cite actual IDs/numbers from the \
data where relevant). No markdown headers, just plain prose."""

ID_PATTERN = re.compile(r"\b([A-Z]{2,4}\d{3,6})\b")


def _mock_answer(question: str, result_context: dict) -> str:
    """
    Deterministic fallback so the Q&A panel works without any API key.
    Note: this returns text WITHOUT a "(mock)" prefix -- the caller
    (answer_question) adds that once, consistently, so callers never see a
    doubled-up "(mock) (mock)" label.
    """
    q = question.lower()
    scoring = result_context.get("scoring") or {}
    exceptions = result_context.get("exceptions", [])

    # "Why didn't TXN1006 match?" style questions -- look the ID up directly
    # in this run's own exceptions list rather than falling back to a
    # generic answer, since we actually have the specific reason on hand.
    id_match = ID_PATTERN.search(question.upper())
    if id_match:
        record_id = id_match.group(1)
        hit = next((e for e in exceptions if record_id in str(e.get("id", ""))), None)
        if hit:
            return f"{record_id} is an unresolved exception on the {hit['side']} side: {hit['reason']}"
        all_matches = (
            result_context.get("exact_matches", [])
            + result_context.get("fuzzy_matches", [])
            + result_context.get("llm_matches", [])
        )
        matched_hit = next(
            (m for m in all_matches if record_id in (str(m.get("internal_id", "")) + str(m.get("bank_id", "")))),
            None,
        )
        if matched_hit:
            return f"{record_id} was actually matched successfully to {matched_hit.get('bank_id') or matched_hit.get('internal_id')}, not left as an exception."
        return f"I don't see {record_id} anywhere in this run's data -- double check the ID."

    if "unreconciled" in q or "how much" in q:
        total_exception_amount = sum(e.get("amount") or 0 for e in exceptions)
        return (
            f"There are {len(exceptions)} unresolved exceptions totalling "
            f"roughly {total_exception_amount:,.2f} (in whatever currency your data is in) across them. "
            f"Match rate for this run was {scoring.get('match_rate_pct', 'unknown')}%."
        )
    if "summar" in q:
        return (
            f"This run matched {scoring.get('correct_matches', '?')} records "
            f"correctly ({scoring.get('match_rate_pct', '?')}% match rate), with "
            f"{scoring.get('false_match_rate_pct', '?')}% of matches wrong and "
            f"{len(exceptions)} exceptions left for manual review."
        )
    if "worth checking" in q or "priorit" in q:
        top = exceptions[:3]
        ids = ", ".join(e.get("id", "?") for e in top)
        return f"I'd start with: {ids or 'no exceptions to review'}."
    return "No live provider is configured -- set GROQ_API_KEY (free tier) or ANTHROPIC_API_KEY in .env for full reasoning."


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

    no_key_configured = result.get("error") and "no GROQ_API_KEY" in result["error"]
    prefix = "(mock) " if no_key_configured else f"(mock, live call failed -- {result['error']}) "
    return {"answer": prefix + _mock_answer(question, result_context), "mode": "mock", "provider": None}