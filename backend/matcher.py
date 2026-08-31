"""Two-pass deterministic reconciliation engine (exact and fuzzy matching)."""

from dataclasses import dataclass, field

from rapidfuzz import fuzz

FUZZY_AUTO_THRESHOLD = 90
FUZZY_REVIEW_FLOOR = 55
AMOUNT_TOLERANCE_PCT = 0.02
DATE_TOLERANCE_DAYS = 3


@dataclass
class MatchResult:
    exact_matches: list = field(default_factory=list)
    fuzzy_matches: list = field(default_factory=list)
    needs_llm: list = field(default_factory=list)
    unmatched_internal: list = field(default_factory=list)
    unmatched_bank: list = field(default_factory=list)


def _amount_close(a: float, b: float) -> bool:
    if a == b:
        return True
    tol = max(abs(a), abs(b)) * AMOUNT_TOLERANCE_PCT
    return abs(a - b) <= max(tol, 1.0)


def _date_close(d1: str, d2: str) -> bool:
    from datetime import datetime
    try:
        dt1 = datetime.strptime(d1, "%Y-%m-%d")
        dt2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((dt1 - dt2).days) <= DATE_TOLERANCE_DAYS
    except ValueError:
        return False


def run_matching(internal_df, bank_df) -> MatchResult:
    result = MatchResult()

    internal_records = internal_df.to_dict("records")
    bank_records = bank_df.to_dict("records")

    matched_bank_ids = set()
    remaining_internal = []

    # Pass 1: Exact match on reference and amount
    bank_by_ref = {}
    for b in bank_records:
        bank_by_ref.setdefault(b["reference"], []).append(b)

    for i_rec in internal_records:
        candidates = [
            b for b in bank_by_ref.get(i_rec["reference"], [])
            if b["bank_id"] not in matched_bank_ids
            and b["settled_amount"] == i_rec["amount"]
        ]
        if len(candidates) == 1:
            b_rec = candidates[0]
            matched_bank_ids.add(b_rec["bank_id"])
            result.exact_matches.append({
                "internal_id": i_rec["internal_id"],
                "bank_id": b_rec["bank_id"],
                "merchant_name": i_rec["merchant_name"],
                "amount": i_rec["amount"],
                "settled_amount": b_rec["settled_amount"],
                "confidence": 100,
                "method": "exact",
                "reason": f"Reference '{i_rec['reference']}' and amount matched exactly on both sides -- no ambiguity to resolve.",
            })
        else:
            remaining_internal.append(i_rec)

    remaining_bank = [b for b in bank_records if b["bank_id"] not in matched_bank_ids]

    # Pass 2: Fuzzy match on name, amount tolerance, and date tolerance
    still_unmatched_internal = []
    used_bank_ids = set()

    for i_rec in remaining_internal:
        best_score = -1
        best_bank = None
        for b_rec in remaining_bank:
            if b_rec["bank_id"] in used_bank_ids:
                continue
            if not _amount_close(i_rec["amount"], b_rec["settled_amount"]):
                continue
            if not _date_close(i_rec["date"], b_rec["value_date"]):
                continue
            name_score = fuzz.token_sort_ratio(i_rec["merchant_name"], b_rec["narration"])
            if name_score > best_score:
                best_score = name_score
                best_bank = b_rec

        if best_bank is None:
            still_unmatched_internal.append(i_rec)
            continue

        pair = {
            "internal_id": i_rec["internal_id"],
            "bank_id": best_bank["bank_id"],
            "merchant_name": i_rec["merchant_name"],
            "bank_narration": best_bank["narration"],
            "amount": i_rec["amount"],
            "settled_amount": best_bank["settled_amount"],
            "confidence": round(best_score, 1),
        }

        if best_score >= FUZZY_AUTO_THRESHOLD:
            used_bank_ids.add(best_bank["bank_id"])
            pair["method"] = "fuzzy"
            pair["reason"] = (
                f"No matching reference number, but merchant name scored {round(best_score,1)}% "
                f"similar and amount/date fell within tolerance -- confident enough to auto-match."
            )
            result.fuzzy_matches.append(pair)
        elif best_score >= FUZZY_REVIEW_FLOOR:
            pair["method"] = "fuzzy_candidate"
            result.needs_llm.append(pair)
            used_bank_ids.add(best_bank["bank_id"])
        else:
            still_unmatched_internal.append(i_rec)

    result.unmatched_internal = still_unmatched_internal
    result.unmatched_bank = [
        b for b in remaining_bank if b["bank_id"] not in used_bank_ids
    ]

    return result
