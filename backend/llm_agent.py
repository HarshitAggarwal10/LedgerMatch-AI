"""LLM-based reconciliation for ambiguous transaction pairs."""

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
    """Fallback heuristic decision when no LLM API is configured."""
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
    """Resolve an ambiguous pair using LLM with fallback to heuristic logic."""
    user_prompt = _build_user_prompt(internal_record, bank_record)
    result = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=1000)

    if result["text"] is not None:
        try:
            text = result["text"].removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            decision = json.loads(text)
            decision["mode"] = "live"
            decision["provider"] = result["provider"]
            return decision
        except (json.JSONDecodeError, KeyError):
            pass

    decision = _mock_decision(internal_record, bank_record)
    decision["mode"] = "mock"
    if result.get("error") and "no GROQ_API_KEY" not in result["error"]:
        decision["reason"] = f"(mock, live call failed -- {result['error']}) " + decision["reason"]
    return decision
