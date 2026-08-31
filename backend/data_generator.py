"""Synthetic financial dataset generator with reconciliation test cases."""

import random
import uuid
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

MERCHANT_POOL = [
    "Bluewave Traders", "Kalyan Textiles Pvt Ltd", "Orbit Logistics",
    "Sundar Foods", "Nimbus Cloud Services", "Ganga Steel Works",
    "Prakash Electricals", "Vertex Consulting", "Coral Retail Group",
    "Amber Interiors", "Zenith Motors", "Harbor Freight Co",
    "Rajlaxmi Enterprises", "Nova Health Systems", "Everest Traders",
]

TYPO_SWAPS = {
    "Pvt Ltd": ["Private Limited", "P Ltd", "Pvt. Ltd."],
    "Services": ["Svcs", "Service"],
    "Traders": ["Trading Co", "Trdrs"],
    "Enterprises": ["Enterp", "Ent."],
}


def _apply_typo(name: str) -> str:
    out = name
    for full, variants in TYPO_SWAPS.items():
        if full in out:
            out = out.replace(full, random.choice(variants))
            return out
    words = out.split()
    if len(words) > 1 and random.random() < 0.5:
        return " ".join(words[:-1])
    return out.upper() if random.random() < 0.3 else out


def generate_dataset(n_records: int = 60, seed: int | None = None):
    """Generate synthetic internal, bank, and gateway datasets with an answer key."""
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    base_date = datetime(2026, 7, 1)
    internal_rows = []
    bank_rows = []
    gateway_rows = []
    answer_rows = []

    n_clean = int(n_records * 0.45)
    n_typo_noref = int(n_records * 0.15)
    n_amount_drift_noref = int(n_records * 0.10)
    n_date_shift_noref = int(n_records * 0.08)
    n_hard_ambiguous = int(n_records * 0.10)
    n_duplicate = int(n_records * 0.05)
    n_missing = n_records - (
        n_clean + n_typo_noref + n_amount_drift_noref + n_date_shift_noref
        + n_hard_ambiguous + n_duplicate
    )

    plan = (
        ["clean"] * n_clean
        + ["typo_noref"] * n_typo_noref
        + ["amount_drift_noref"] * n_amount_drift_noref
        + ["date_shift_noref"] * n_date_shift_noref
        + ["hard_ambiguous"] * n_hard_ambiguous
        + ["duplicate"] * n_duplicate
        + ["missing"] * n_missing
    )
    random.shuffle(plan)

    for i, kind in enumerate(plan):
        internal_id = f"TXN{1000 + i}"
        bank_id = f"STL{5000 + i}"
        merchant = random.choice(MERCHANT_POOL)
        amount = round(random.uniform(1500, 185000), 2)
        date = base_date + timedelta(days=random.randint(0, 45))

        internal_rows.append({
            "internal_id": internal_id,
            "date": date.strftime("%Y-%m-%d"),
            "merchant_name": merchant,
            "amount": amount,
            "reference": internal_id,
        })

        if kind == "clean":
            bank_rows.append({
                "bank_id": bank_id,
                "value_date": date.strftime("%Y-%m-%d"),
                "narration": merchant,
                "settled_amount": amount,
                "reference": internal_id,
            })
            answer_rows.append({"internal_id": internal_id, "bank_id": bank_id,
                                 "mismatch_type": "none"})

        elif kind == "typo_noref":
            bank_rows.append({
                "bank_id": bank_id,
                "value_date": date.strftime("%Y-%m-%d"),
                "narration": _apply_typo(merchant),
                "settled_amount": amount,
                "reference": f"REF{uuid.uuid4().hex[:6].upper()}",
            })
            answer_rows.append({"internal_id": internal_id, "bank_id": bank_id,
                                 "mismatch_type": "name_typo_no_reference"})

        elif kind == "amount_drift_noref":
            fee = round(random.uniform(2, 45), 2)
            bank_rows.append({
                "bank_id": bank_id,
                "value_date": date.strftime("%Y-%m-%d"),
                "narration": merchant,
                "settled_amount": round(amount - fee, 2),
                "reference": f"REF{uuid.uuid4().hex[:6].upper()}",
            })
            answer_rows.append({"internal_id": internal_id, "bank_id": bank_id,
                                 "mismatch_type": "amount_drift_fee_no_reference"})

        elif kind == "date_shift_noref":
            shifted = date + timedelta(days=random.choice([1, 2, 3]))
            bank_rows.append({
                "bank_id": bank_id,
                "value_date": shifted.strftime("%Y-%m-%d"),
                "narration": merchant,
                "settled_amount": amount,
                "reference": f"REF{uuid.uuid4().hex[:6].upper()}",
            })
            answer_rows.append({"internal_id": internal_id, "bank_id": bank_id,
                                 "mismatch_type": "date_shift_no_reference"})

        elif kind == "hard_ambiguous":
            fee = round(random.uniform(5, 60), 2)
            bank_rows.append({
                "bank_id": bank_id,
                "value_date": date.strftime("%Y-%m-%d"),
                "narration": _apply_typo(merchant),
                "settled_amount": round(amount - fee, 2),
                "reference": f"REF{uuid.uuid4().hex[:6].upper()}",
            })
            answer_rows.append({"internal_id": internal_id, "bank_id": bank_id,
                                 "mismatch_type": "hard_ambiguous_stacked"})

        elif kind == "duplicate":
            bank_rows.append({
                "bank_id": bank_id,
                "value_date": date.strftime("%Y-%m-%d"),
                "narration": merchant,
                "settled_amount": amount,
                "reference": internal_id,
            })
            dup_id = f"STL{5000 + i}D"
            bank_rows.append({
                "bank_id": dup_id,
                "value_date": date.strftime("%Y-%m-%d"),
                "narration": merchant,
                "settled_amount": amount,
                "reference": internal_id,
            })
            answer_rows.append({"internal_id": internal_id, "bank_id": bank_id,
                                 "mismatch_type": "duplicate_settlement"})

        elif kind == "missing":
            answer_rows.append({"internal_id": internal_id, "bank_id": None,
                                 "mismatch_type": "missing_from_bank"})

        gateway_should_exist = kind not in ("hard_ambiguous",) and not (
            kind == "missing" and random.random() < 0.5
        )
        if gateway_should_exist:
            gw_fee = round(amount * 0.019 + 2, 2)
            gateway_rows.append({
                "gateway_id": f"GTW{7000 + i}",
                "txn_time": date.strftime("%Y-%m-%d"),
                "payee_name": merchant,
                "gateway_amount": round(amount - gw_fee, 2),
                "gateway_fee": gw_fee,
                "reference": internal_id,
            })

    for j in range(2):
        bank_id = f"STL{6000 + j}"
        merchant = random.choice(MERCHANT_POOL)
        date = base_date + timedelta(days=random.randint(0, 45))
        bank_rows.append({
            "bank_id": bank_id,
            "value_date": date.strftime("%Y-%m-%d"),
            "narration": merchant,
            "settled_amount": round(random.uniform(1500, 50000), 2),
            "reference": f"UNKNOWN{j}",
        })
        answer_rows.append({"internal_id": None, "bank_id": bank_id,
                             "mismatch_type": "missing_from_internal"})

    missing_rows = [r for r, a in zip(internal_rows, answer_rows) if a["mismatch_type"] == "missing_from_bank"]
    if missing_rows:
        target = random.choice(missing_rows)
        trap_amount = round(target["amount"] * random.uniform(1.015, 1.025), 2)
        bank_rows.append({
            "bank_id": "STL6099",
            "value_date": target["date"],
            "narration": target["merchant_name"],
            "settled_amount": trap_amount,
            "reference": "UNKNOWNTRAP",
        })
        answer_rows.append({"internal_id": None, "bank_id": "STL6099",
                             "mismatch_type": "lookalike_trap_should_not_match"})

    internal_df = pd.DataFrame(internal_rows)
    bank_df = pd.DataFrame(bank_rows)
    gateway_df = pd.DataFrame(gateway_rows)
    answer_df = pd.DataFrame(answer_rows)
    return internal_df, bank_df, gateway_df, answer_df


if __name__ == "__main__":
    internal_df, bank_df, gateway_df, answer_df = generate_dataset(60)
    internal_df.to_csv("../sample_data/internal_ledger.csv", index=False)
    bank_df.to_csv("../sample_data/bank_settlements.csv", index=False)
    gateway_df.to_csv("../sample_data/gateway_settlements.csv", index=False)
    answer_df.to_csv("../sample_data/answer_key.csv", index=False)
    print(f"internal: {len(internal_df)} rows, bank: {len(bank_df)} rows, "
          f"gateway: {len(gateway_df)} rows, answer key: {len(answer_df)} rows")
