"""
evaluator.py
------------
Scores the pipeline's matches against the known ground truth (answer_key).
This only works because data_generator.py records the true mapping when it
creates the synthetic mismatches -- in a real deployment you would not have
this, which is exactly why the exception list matters so much more than the
match rate alone.

Reports:
  - match_rate:        % of true matches the pipeline found correctly
  - false_match_rate:  % of the pipeline's matches that were WRONG
                        (the expensive kind of mistake in real finance)
  - exceptions:        every record the pipeline left unresolved, each with
                        a plain-English reason
"""


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
    }
