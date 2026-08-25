"""
gateway_matcher.py
-------------------
Stage 2 of reconciliation: brings in the THIRD source (payment gateway
settlement report) and reconciles it against records already resolved
between internal <-> bank.

Because the gateway reference is modelled as reliable (unlike the bank
feed), this stage matches primarily on reference, with a fuzzy fallback on
merchant name + amount (accounting for the gateway's processing fee) for
anything that doesn't line up on reference alone.

Every record ends up with a three_way_status:
  - "full_match"     : internal, bank, AND gateway all agree
  - "partial_match"  : internal + bank agree, but no corresponding gateway
                        record found (or vice versa) -- flagged, not hidden
  - "gateway_only"    : gateway shows a settlement with no internal/bank
                        counterpart at all
"""

from rapidfuzz import fuzz

GATEWAY_FEE_TOLERANCE_PCT = 0.035  # fee typically ~1.9-2.5%, allow some slack
NAME_MATCH_FLOOR = 70


def _fee_consistent(internal_amount: float, gateway_amount: float) -> bool:
    if internal_amount <= 0:
        return False
    implied_fee_pct = (internal_amount - gateway_amount) / internal_amount
    return -0.01 <= implied_fee_pct <= GATEWAY_FEE_TOLERANCE_PCT + 0.02


def reconcile_with_gateway(resolved_records: list, gateway_df) -> dict:
    """
    resolved_records: list of dicts, each with at minimum
        internal_id, merchant_name, amount   (the two-way matched/exception
        records coming out of the internal<->bank stage)

    Returns {
      "full_match": [...],
      "partial_match": [...],   # each annotated with why gateway didn't confirm
      "gateway_only": [...],    # gateway records with no internal counterpart
    }
    """
    gateway_records = gateway_df.to_dict("records")
    gateway_by_ref = {}
    for g in gateway_records:
        gateway_by_ref.setdefault(g["reference"], []).append(g)

    used_gateway_ids = set()
    full_match = []
    partial_match = []

    for rec in resolved_records:
        candidates = gateway_by_ref.get(rec["internal_id"], [])
        candidates = [g for g in candidates if g["gateway_id"] not in used_gateway_ids]

        chosen = None
        if candidates:
            # reference matched -- just sanity-check the fee makes sense
            for g in candidates:
                if _fee_consistent(rec["amount"], g["gateway_amount"]):
                    chosen = g
                    break
            if chosen is None:
                chosen = candidates[0]  # reference matched but fee looks odd; still surface it
        else:
            # no reference hit -- fall back to name + fee-consistent amount
            best_score = -1
            for g in gateway_records:
                if g["gateway_id"] in used_gateway_ids:
                    continue
                if not _fee_consistent(rec["amount"], g["gateway_amount"]):
                    continue
                score = fuzz.token_sort_ratio(rec["merchant_name"], g["payee_name"])
                if score > best_score:
                    best_score = score
                    chosen = g
            if best_score < NAME_MATCH_FLOOR:
                chosen = None

        if chosen is not None:
            used_gateway_ids.add(chosen["gateway_id"])
            implied_fee_pct = round(
                100 * (rec["amount"] - chosen["gateway_amount"]) / rec["amount"], 2
            ) if rec["amount"] else 0
            full_match.append({
                **rec,
                "gateway_id": chosen["gateway_id"],
                "gateway_amount": chosen["gateway_amount"],
                "implied_fee_pct": implied_fee_pct,
                "three_way_status": "full_match",
            })
        else:
            partial_match.append({
                **rec,
                "gateway_id": None,
                "three_way_status": "partial_match",
                "gateway_note": "No corresponding gateway settlement found -- internal/bank agree, but this transaction never shows up at the gateway layer. Worth checking for a missed webhook or a manual ledger entry.",
            })

    gateway_only = [
        {
            "gateway_id": g["gateway_id"],
            "merchant_name": g["payee_name"],
            "amount": g["gateway_amount"],
            "three_way_status": "gateway_only",
            "gateway_note": "Gateway shows a settlement with no matching internal or bank record at all.",
        }
        for g in gateway_records
        if g["gateway_id"] not in used_gateway_ids
    ]

    return {
        "full_match": full_match,
        "partial_match": partial_match,
        "gateway_only": gateway_only,
    }
