"""
llm_agent.py
------------
This is the genuinely "agentic" part of the pipeline. Everything upstream
(matcher.py) is deterministic rule-based logic -- fast, cheap, explainable,
but it can't make judgment calls. Whatever it can't confidently resolve gets
handed to an LLM, which looks at both records side by side and reasons
about whether they're the same underlying transaction, the way a human
analyst would when a fuzzy-match score alone isn't conclusive.

Provider order: Groq -> Claude -> mock (see llm_provider.py). Mock
decisions are always clearly labelled as such -- never silently
substituted for a real one.
"""

import json

from llm_provider import call_llm

SYSTEM_PROMPT = """You are a finance reconciliation analyst. You will be shown \
two transaction records -- one from an internal payments ledger, one from a \
bank settlement file -- that a rule-based matcher flagged as a *possible* \
match but could not confirm automatically.

Decide whether they represent the same underlying transaction. Consider the \
merchant name (allowing for abbreviations, legal suffixes, or minor typos), \
the amount (allowing for small settlement fees), and the date (allowing for \
bank processing delay of a few days).

Respond with ONLY a JSON object, no other text, no markdown code fences, in \
this exact shape:
{"decision": "match" | "no_match" | "uncertain", "confidence": <0-100 integer>, "reason": "<one plain-English sentence>"}"""


def _build_user_prompt(internal_record: dict, bank_record: dict) -> str:
    return (
        "Internal ledger record:\n"
        f"  Merchant: {internal_record['merchant_name']}\n"
        f"  Amount: {internal_record['amount']}\n"
        f"  Date: {internal_record['date']}\n\n"
        "Bank settlement record:\n"
        f"  Narration: {bank_record.get('bank_narration', bank_record.get('narration'))}\n"
        f"  Settled amount: {bank_record['settled_amount']}\n\n"
        "Are these the same transaction?"
    )


def _mock_decision(internal_record: dict, bank_record: dict) -> dict:
    """
    A transparent, non-LLM fallback so the app runs without any API key.
    Uses the same signal a human glancing at the pair would: name overlap
    and amount closeness. This is intentionally simple -- it exists so the
    UI and pipeline are fully testable, not to imitate the real model.
    """
    name_a = internal_record["merchant_name"].lower()
    name_b = str(bank_record.get("bank_narration", bank_record.get("narration", ""))).lower()
    overlap = len(set(name_a.split()) & set(name_b.split()))
    amount_diff_pct = abs(internal_record["amount"] - bank_record["settled_amount"]) / max(
        internal_record["amount"], 1
    )

    if overlap >= 1 and amount_diff_pct < 0.03:
        return {
            "decision": "match",
            "confidence": 78,
            "reason": "(mock) Merchant names share key terms and amounts are within a normal fee tolerance.",
        }
    if overlap == 0 and amount_diff_pct > 0.05:
        return {
            "decision": "no_match",
            "confidence": 65,
            "reason": "(mock) No shared merchant terms and amounts diverge beyond a plausible fee.",
        }
    return {
        "decision": "uncertain",
        "confidence": 40,
        "reason": "(mock) Partial signal only -- would need a human or a live LLM to confirm.",
    }


def resolve_pair(internal_record: dict, bank_record: dict) -> dict:
    """Returns a decision dict with an added 'mode': 'live' or 'mock'."""
    user_prompt = _build_user_prompt(internal_record, bank_record)
    result = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=200)

    if result["text"] is not None:
        try:
            text = result["text"].removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            decision = json.loads(text)
            decision["mode"] = "live"
            decision["provider"] = result["provider"]
            return decision
        except (json.JSONDecodeError, KeyError):
            # live call succeeded but didn't return parseable JSON -- fall
            # through to mock rather than crash the pipeline on one record
            pass

    decision = _mock_decision(internal_record, bank_record)
    decision["mode"] = "mock"
    if result.get("error") and "no GROQ_API_KEY" not in result["error"]:
        decision["reason"] = f"(mock, live call failed -- {result['error']}) " + decision["reason"]
    return decision
