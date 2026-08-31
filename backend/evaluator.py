"""Evaluation metrics comparing match results against ground truth."""


def evaluate(match_result, answer_key_df, internal_df, bank_df):
    true_map = {
        row["internal_id"]: row["bank_id"]
        for row in answer_key_df.to_dict("records")
        if row["internal_id"] is not None
    }

    all_predicted = (
        match_result.exact_matches
        + match_result.fuzzy_matches
        + [p for p in match_result.llm_matches if p["llm_decision"] == "match"]
    )

    correct = 0
    false_matches = []
    for pred in all_predicted:
        true_bank_id = true_map.get(pred["internal_id"])
        if true_bank_id == pred["bank_id"]:
            correct += 1
        else:
            false_matches.append(pred)

    total_true_matches = sum(1 for v in true_map.values() if v is not None)
    match_rate = round(100 * correct / total_true_matches, 1) if total_true_matches else 0.0
    false_match_rate = (
        round(100 * len(false_matches) / len(all_predicted), 1) if all_predicted else 0.0
    )

    total_internal = len(internal_df)
    total_bank = len(bank_df)

    trap_case = _evaluate_trap_case(answer_key_df, all_predicted)

    return {
        "total_internal_records": total_internal,
        "total_bank_records": total_bank,
        "total_true_matches": total_true_matches,
        "auto_matched": len(match_result.exact_matches) + len(match_result.fuzzy_matches),
        "llm_resolved": sum(1 for p in match_result.llm_matches if p["llm_decision"] == "match"),
        "correct_matches": correct,
        "match_rate_pct": match_rate,
        "false_matches": false_matches,
        "false_match_rate_pct": false_match_rate,
        "total_exceptions": (
            len(match_result.unmatched_internal)
            + len(match_result.unmatched_bank)
            + sum(1 for p in match_result.llm_matches if p["llm_decision"] != "match")
        ),
        "trap_case": trap_case,
    }


def _evaluate_trap_case(answer_key_df, all_predicted):
    """Evaluate whether the pipeline matched the planted lookalike record."""
    trap_rows = answer_key_df[answer_key_df["mismatch_type"] == "lookalike_trap_should_not_match"]
    if trap_rows.empty:
        return None

    trap_bank_id = trap_rows.iloc[0]["bank_id"]
    fooled_by = next((p for p in all_predicted if p["bank_id"] == trap_bank_id), None)

    if fooled_by is None:
        return {
            "bank_id": trap_bank_id,
            "was_fooled": False,
            "matched_internal_id": None,
        }
    return {
        "bank_id": trap_bank_id,
        "was_fooled": True,
        "matched_internal_id": fooled_by["internal_id"],
    }
