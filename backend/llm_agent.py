"""
llm_agent.py
------------
This is the genuinely "agentic" part of the pipeline. Everything upstream
(matcher.py) is deterministic rule-based logic -- fast, cheap, explainable,
but it can't make judgment calls. Whatever it can't confidently resolve gets
handed to Claude, which looks at both records side by side and reasons about
whether they're the same underlying transaction, the way a human analyst
would when a fuzzy-match score alone isn't conclusive.

Two modes:
  - LIVE mode: calls the real Claude API. Requires ANTHROPIC_API_KEY.
  - MOCK mode: runs automatically if no API key is set, so the app is fully
    demoable without spending API credits. Mock decisions are clearly
    labelled as such everywhere in the UI -- never silently substituted.
"""

import json
import os

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a finance reconciliation analyst. You will be shown \
two transaction records -- one from an internal payments ledger, one from a \
bank settlement file -- that a rule-based matcher flagged as a *possible* \
match but could not confirm automatically.

Decide whether they represent the same underlying transaction. Consider the \
merchant name (allowing for abbreviations, legal suffixes, or minor typos), \
the amount (allowing for small settlement fees), and the date (allowing for \
bank processing delay of a few days).

Respond with ONLY a JSON object, no other text, in this exact shape:
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
    A transparent, non-LLM fallback so the app runs without an API key.
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
        "reason": "(mock) Partial signal only -- would need a human or the live LLM to confirm.",
    }


def resolve_pair(internal_record: dict, bank_record: dict) -> dict:
    """Returns a decision dict. Adds 'mode': 'live' or 'mock' to the result."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        decision = _mock_decision(internal_record, bank_record)
        decision["mode"] = "mock"
        return decision

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(internal_record, bank_record)}],
        )
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        decision = json.loads(text)
        decision["mode"] = "live"
        return decision
    except Exception as e:
        # Never let an API hiccup crash the pipeline -- fall back to mock
        # and say exactly what happened, which is itself the "handled
        # failure gracefully" the project needs to demonstrate.
        decision = _mock_decision(internal_record, bank_record)
        decision["mode"] = "mock"
        decision["reason"] = f"(mock, live call failed: {type(e).__name__}) " + decision["reason"]
        return decision
