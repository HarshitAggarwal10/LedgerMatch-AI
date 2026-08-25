"""
main.py
-------
LedgerMatch AI backend. Endpoints:

  POST /api/reconcile/sample   -> generates a fresh synthetic 3-source batch
                                   (internal ledger, bank, gateway) on the
                                   fly and reconciles it, with scoring since
                                   we know the ground truth we made.
  POST /api/reconcile/upload   -> reconciles two user-uploaded CSVs
                                   (internal ledger + bank statement).
                                   No scoring, since there's no answer key
                                   for real data.
  POST /api/ask                -> Settlement Q&A: answers a question about
                                   a specific run, grounded in that run's data.
  GET  /api/health             -> reports whether the LLM agent is running
                                   live (API key set) or in mock mode.

Run with:  uvicorn main:app --reload --port 8000
"""

import io
import os

import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from data_generator import generate_dataset
from pipeline import run_pipeline
from qa_agent import answer_question

app = FastAPI(title="LedgerMatch AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/reconcile/sample")
def reconcile_sample(n_records: int = 60):
    internal_df, bank_df, gateway_df, answer_df = generate_dataset(n_records)
    result = run_pipeline(internal_df, bank_df, gateway_df=gateway_df, answer_key_df=answer_df)
    result["internal_preview"] = internal_df.head(8).to_dict("records")
    result["bank_preview"] = bank_df.head(8).to_dict("records")
    return result


@app.post("/api/reconcile/upload")
async def reconcile_upload(
    internal_file: UploadFile = File(...),
    bank_file: UploadFile = File(...),
):
    internal_bytes = await internal_file.read()
    bank_bytes = await bank_file.read()
    internal_df = pd.read_csv(io.BytesIO(internal_bytes))
    bank_df = pd.read_csv(io.BytesIO(bank_bytes))

    required_internal = {"internal_id", "date", "merchant_name", "amount", "reference"}
    required_bank = {"bank_id", "value_date", "narration", "settled_amount", "reference"}
    missing_i = required_internal - set(internal_df.columns)
    missing_b = required_bank - set(bank_df.columns)
    if missing_i or missing_b:
        return {
            "error": "Column mismatch.",
            "missing_internal_columns": sorted(missing_i),
            "missing_bank_columns": sorted(missing_b),
            "expected_internal_columns": sorted(required_internal),
            "expected_bank_columns": sorted(required_bank),
        }

    # no gateway file for user uploads yet -- two-source reconciliation only
    result = run_pipeline(internal_df, bank_df, gateway_df=None, answer_key_df=None)
    return result


class AskRequest(BaseModel):
    question: str
    result_context: dict


@app.post("/api/ask")
def ask(req: AskRequest):
    return answer_question(req.question, req.result_context)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_mode": "live" if os.environ.get("ANTHROPIC_API_KEY") else "mock",
    }


# --- serve the built React frontend ----------------------------------------
# `npm run build` in ../frontend produces ../frontend/dist. Mounted at root
# with html=True so "/" serves index.html and asset paths resolve directly.
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")
