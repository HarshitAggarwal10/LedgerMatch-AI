"""
pipeline.py
-----------
Wires matcher.py -> llm_agent.py -> gateway_matcher.py -> evaluator.py into
one call, and shapes the output into exactly what the frontend needs: a
summary (including throughput), a matched table, a three-way reconciliation
breakdown, and an exceptions table with a human-readable reason for every
single unresolved record. Nothing here rounds numbers up or hides a bad
case -- if the pipeline can't resolve something, it says so.
"""

import time

from matcher import run_matching
from llm_agent import resolve_pair
from gateway_matcher import reconcile_with_gateway


def run_pipeline(internal_df, bank_df, gateway_df=None, answer_key_df=None):
    start_time = time.perf_counter()

    match_result = run_matching(internal_df, bank_df)

    # --- Resolve the ambiguous middle ground with the LLM agent -----------
    llm_matches = []
    for pair in match_result.needs_llm:
        i_rec = {
            "merchant_name": pair["merchant_name"],
            "amount": pair["amount"],
            "date": next(
                (r["date"] for r in internal_df.to_dict("records")
                 if r["internal_id"] == pair["internal_id"]),
                "",
            ),
        }
        b_rec = {
            "bank_narration": pair["bank_narration"],
            "settled_amount": pair["settled_amount"],
        }
        decision = resolve_pair(i_rec, b_rec)
        llm_matches.append({
            **pair,
            "llm_decision": decision["decision"],
            "llm_confidence": decision["confidence"],
            "llm_reason": decision["reason"],
            "llm_mode": decision["mode"],
        })
    match_result.llm_matches = llm_matches

    # --- Build the exceptions list (every unresolved record, with a reason)
    exceptions = []
    for rec in match_result.unmatched_internal:
        exceptions.append({
            "side": "internal",
            "id": rec["internal_id"],
            "merchant_name": rec["merchant_name"],
            "amount": rec["amount"],
            "reason": "No plausible bank-side match found within amount/date/name tolerance.",
        })
    for rec in match_result.unmatched_bank:
        exceptions.append({
            "side": "bank",
            "id": rec["bank_id"],
            "merchant_name": rec["narration"],
            "amount": rec["settled_amount"],
            "reason": "Bank shows a settlement with no corresponding internal ledger record.",
        })
    for pair in llm_matches:
        if pair["llm_decision"] != "match":
            exceptions.append({
                "side": "ambiguous",
                "id": f"{pair['internal_id']} / {pair['bank_id']}",
                "merchant_name": pair["merchant_name"],
                "amount": pair["amount"],
                "reason": f"[{pair['llm_mode']}] {pair['llm_reason']}",
            })

    result = {
        "exact_matches": match_result.exact_matches,
        "fuzzy_matches": match_result.fuzzy_matches,
        "llm_matches": [p for p in llm_matches if p["llm_decision"] == "match"],
        "exceptions": exceptions,
    }

    if answer_key_df is not None:
        from evaluator import evaluate
        result["scoring"] = evaluate(match_result, answer_key_df, internal_df, bank_df)
    else:
        result["scoring"] = None

    # --- Stage 2: bring in the third source (gateway settlements) ---------
    if gateway_df is not None and len(gateway_df) > 0:
        two_way_resolved = (
            [{"internal_id": m["internal_id"], "merchant_name": m["merchant_name"], "amount": m["amount"]}
             for m in match_result.exact_matches]
            + [{"internal_id": m["internal_id"], "merchant_name": m["merchant_name"], "amount": m["amount"]}
               for m in match_result.fuzzy_matches]
            + [{"internal_id": m["internal_id"], "merchant_name": m["merchant_name"], "amount": m["amount"]}
               for m in llm_matches if m["llm_decision"] == "match"]
        )
        gateway_result = reconcile_with_gateway(two_way_resolved, gateway_df)
        result["gateway_reconciliation"] = gateway_result
    else:
        result["gateway_reconciliation"] = None

    elapsed_seconds = round(time.perf_counter() - start_time, 4)
    total_records = len(internal_df) + len(bank_df) + (len(gateway_df) if gateway_df is not None else 0)
    result["performance"] = {
        "elapsed_seconds": elapsed_seconds,
        "total_records_processed": total_records,
        "records_per_second": round(total_records / elapsed_seconds, 1) if elapsed_seconds > 0 else None,
    }

    return result
