"""FastAPI application entry point and routing."""

import io
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

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
def reconcile_sample(n_records: int = 60, seed: int | None = None):
    internal_df, bank_df, gateway_df, answer_df = generate_dataset(n_records, seed=seed)
    result = run_pipeline(internal_df, bank_df, gateway_df=gateway_df, answer_key_df=answer_df)
    result["internal_preview"] = internal_df.head(8).to_dict("records")
    result["bank_preview"] = bank_df.head(8).to_dict("records")
    result["seed_used"] = seed
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
    if os.environ.get("GROQ_API_KEY"):
        return {"status": "ok", "llm_mode": "live", "provider": "groq"}
    return {"status": "ok", "llm_mode": "mock", "provider": None}


app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")
