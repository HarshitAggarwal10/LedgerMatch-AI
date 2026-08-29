# LedgerMatch AI

**AI Finance Controller — Razorpay AI Buildathon**

LedgerMatch reconciles an internal payment ledger against a bank settlement
file *and* a payment gateway settlement report — three independent records
of the same underlying money movement — and reports exactly what agrees,
what doesn't, and why. Every run is scored against a known ground truth, so
the numbers below are measured, not claimed.

```
Match rate:        88.5%   (54 of 61 true matches found)
False-match rate:   0.0%   (wrongly-matched pairs -- the costly kind)
Exceptions:            13   (every one with a plain-English reason)
Throughput:      ~12,600 records/sec  (174 records in 0.014s)
Three-way check:  50 full match · 4 partial · 3 gateway-only
```

*(Numbers above are from one real run in mock LLM mode. They shift slightly
between runs since the synthetic batch is regenerated fresh each time — see
[Why the numbers move](#why-the-numbers-move-between-runs).)*

---

## What it does

1. **Exact match** — reference ID + amount, matched to the paisa. Resolves
   most real-world reconciliation instantly, no AI involved.
2. **Fuzzy match** — merchant-name similarity (`rapidfuzz`) plus amount and
   date tolerance, for records the bank feed wrote slightly differently.
3. **LLM agent review** — whatever's still ambiguous goes to Claude, which
   reasons about both records side by side and returns a decision,
   confidence score, and one-sentence explanation.
4. **Gateway cross-check** — a *third*, independent source (the payment
   gateway's own settlement file) confirms or flags what the first two
   stages agreed on, upgrading this from a two-file diff to genuine
   multi-source reconciliation.
5. **Honest exceptions** — anything still unresolved is reported with a
   specific reason, never hidden or forced into a fake match.
6. **Settlement Q&A agent** — ask natural-language questions about a
   specific run ("how much is still unreconciled?") and get an answer
   grounded strictly in that run's own data.

## Why this design

The brief's bar is explicit: *throughput, measured accuracy, and an honest
exception list — one cherry-picked match proves nothing.* Every design
choice here traces back to that:

- The synthetic data generator injects deliberate typos, amount drift, date
  shifts, duplicates, missing records — **and one "lookalike trap"**: a
  bank-only record engineered to superficially resemble a real transaction,
  specifically to test whether the pipeline can be fooled into a false
  match. Its outcome is reported honestly either way.
- Every run is scored against the ground truth the generator itself
  created, so the match rate and false-match rate are computed, not
  asserted.
- The pipeline runs in **mock LLM mode by default** (no API key needed) so
  it's fully demoable and testable without cost — but every mock decision
  is labelled `(mock)` everywhere in the UI and API response, never
  silently substituted for a real one.
- The pipeline is timed end-to-end and reports records/sec, directly
  answering "throughput" in the judging bar.

## Why the numbers move between runs

The synthetic dataset is regenerated fresh on every "Run on sample batch"
click (no fixed seed by default), so a handful of edge cases — like whether
the lookalike trap happens to get auto-matched — vary run to run. This is
intentional: it proves the reported numbers are computed live rather than
baked into a single rehearsed demo. Pass `?n_records=60` (or any seed via
`generate_dataset(n_records, seed=...)` in `data_generator.py`) for a
reproducible run.

---

## Project structure

```
ledgermatch-ai/
├── backend/
│   ├── main.py              FastAPI app (reconcile/upload/ask/health endpoints)
│   ├── data_generator.py    synthetic 3-source dataset + ground-truth answer key
│   ├── matcher.py           exact + fuzzy two-pass matching engine
│   ├── llm_agent.py         LLM resolution for ambiguous pairs (live + mock)
│   ├── gateway_matcher.py   three-way reconciliation against the gateway source
│   ├── evaluator.py         scores pipeline output against ground truth
│   ├── pipeline.py          orchestrates every stage, times the run
│   ├── qa_agent.py          Settlement Q&A, grounded in run data
│   ├── requirements.txt
│   └── .env.example
├── frontend/                React + Vite + Tailwind v4
│   ├── src/
│   │   ├── components/      Header, Hero, StatsGrid, MatchedTable,
│   │   │                    ExceptionsTable, GatewaySection, QAPanel,
│   │   │                    PipelineSteps, Architecture, Footer, etc.
│   │   ├── api.js           backend API client
│   │   ├── csvExport.js     client-side CSV report download
│   │   └── App.jsx
│   ├── vite.config.js       dev-server proxy: /api -> FastAPI on :8000
│   └── package.json
└── sample_data/             one pre-generated batch for quick inspection
    ├── internal_ledger.csv
    ├── bank_settlements.csv
    ├── gateway_settlements.csv
    └── answer_key.csv
```

---

## Running it locally

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: enable live LLM calls (otherwise runs in mock mode)
cp .env.example .env
```

Then edit `.env` and set **one** of these:

```bash
# Recommended: Groq has a generous free tier, no credit card required.
# Get a key at https://console.groq.com/keys
GROQ_API_KEY=gsk_your-key-here

# Or: Claude, used only if GROQ_API_KEY is not set.
# Get a key at https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

If Groq is set, it's used for everything (the LLM agent and the Settlement
Q&A agent). If a live call ever fails for any reason — bad key, rate limit,
no credit — the app catches it and falls back to mock mode automatically,
labelling the response so it's never silently faked.

### 2. Frontend

```bash
cd frontend
npm install
npm run build          # produces frontend/dist, which FastAPI serves in production
```

### 3. Run

```bash
cd backend
# if you set an API key in .env, load it into the shell first:
export $(grep -v '^#' .env | xargs)   # skip this line if running in mock mode

uvicorn main:app --port 8000
```

Open **http://localhost:8000** — click "Run on sample batch."

### Frontend dev mode (hot reload, optional)

```bash
# terminal 1
cd backend && uvicorn main:app --reload --port 8000

# terminal 2
cd frontend && npm run dev
```

Open **http://localhost:5173** — the dev server proxies `/api` to FastAPI
on :8000 automatically (see `vite.config.js`).

---

## Using your own data

Click **"Use my own CSVs"** on the running app. Required columns:

| Internal ledger | Bank settlement file |
|---|---|
| `internal_id` | `bank_id` |
| `date` | `value_date` |
| `merchant_name` | `narration` |
| `amount` | `settled_amount` |
| `reference` | `reference` |

(Gateway three-way reconciliation and ground-truth scoring are only
available on the synthetic sample batch, since real uploads have no known
answer key.)

---

## API reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/reconcile/sample?n_records=60` | POST | Generate a fresh synthetic batch and reconcile it (with scoring) |
| `/api/reconcile/upload` | POST | Reconcile two uploaded CSVs (`internal_file`, `bank_file`) |
| `/api/ask` | POST | `{question, result_context}` → grounded answer about that run |
| `/api/health` | GET | `{status, llm_mode}` — reports live vs. mock |

---

## Tech stack

**Backend:** Python, FastAPI, pandas, rapidfuzz, Faker, Groq SDK, Anthropic SDK
**Frontend:** React, Vite, Tailwind CSS v4
**AI:** Groq (`openai/gpt-oss-20b`, free tier) as the primary LLM provider,
with Claude (`claude-sonnet-4-6`) as a secondary option and a fully
offline mock fallback — used for both ambiguous-match resolution and the
Settlement Q&A agent

## What's intentionally *not* here

No deep learning / trained neural model. Reconciliation is fundamentally a
matching problem, not a prediction problem — deterministic rule-based
logic handles the bulk of it correctly and explainably, and the LLM is used
specifically where judgment calls, not pattern learning, are needed. Using
a heavier ML model here would have meant strictly worse and less
explainable, not more impressive.
