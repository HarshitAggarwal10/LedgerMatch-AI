# LedgerMatch AI

**Autonomous Multi-Source Reconciliation & Finance Controller Agent**

LedgerMatch AI is an AI-powered finance operations controller designed to close the reconciliation loop across internal payment ledgers, bank settlement feeds, and payment gateway reports. It combines deterministic rule engines with LLM reasoning to resolve ambiguous matches, verify fee tolerances, detect anomalies, and report an honest, auditable list of exceptions.

---

## Key Features

- **Multi-Tier Matching Pipeline**:
  - **Tier 1 (Exact Match)**: Deterministic reference ID and paisa-level amount matching.
  - **Tier 2 (Fuzzy Match)**: Token-sort string similarity (`rapidfuzz`) with configurable amount and date drift tolerance.
  - **Tier 3 (LLM Reasoning Agent)**: Evaluates complex edge cases (abbreviated legal names, fee structures, date delays) using Groq LLM inference, returning structured decisions and explanations.
- **Three-Way Gateway Cross-Check**:
  - Validates settled pairs against payment gateway reports, accounting for gateway commission/fee deductions, identifying missed webhooks or unauthorized entries.
- **Settlement Q&A Agent**:
  - Natural language querying interface grounded strictly in the current reconciliation batch's data.
- **Adversarial Trap Verification & Scoring**:
  - Built-in evaluation engine scores every run against ground-truth answer keys, tracking true match rates, false match rates, and performance against planted lookalike records.
- **Interactive Precision-Recall Explorer**:
  - Client-side confidence threshold adjustment with live recalculation of match rates and confidence histograms.
- **Dual-Mode Operation**:
  - Runs with live Groq LLM inference or an offline deterministic heuristic fallback when no API key is provided.

---

## System Architecture

```
                    +-----------------------------+
                    | Synthetic Data Generator /  |
                    |    Uploaded CSV Datasets    |
                    +--------------+--------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
         v                                                   v
+------------------+                               +--------------------+
| Internal Ledger  |                               |  Bank Settlements  |
+--------+---------+                               +---------+----------+
         |                                                   |
         +-------------------------+-------------------------+
                                   |
                                   v
             +-------------------------------------------+
             | Pass 1: Exact Match Engine                |
             | - Reference ID & exact settled amount     |
             +---------------------+---------------------+
                                   | Unresolved
                                   v
             +-------------------------------------------+
             | Pass 2: Fuzzy Match Engine (rapidfuzz)    |
             | - Name token similarity                   |
             | - Amount & date tolerance windows         |
             +---------------------+---------------------+
                                   | Ambiguous (Score: 55-89)
                                   v
             +-------------------------------------------+
             | Pass 3: LLM Agent Review (Groq API)       |
             | - Pairwise JSON reasoning & explanation   |
             +---------------------+---------------------+
                                   |
                         Resolved Transactions
                                   |
                                   v
             +-------------------------------------------+
             | Stage 4: Gateway Cross-Check (3-Way)      |
             | - Compares against Payment Gateway report |
             | - Validates fee deductions (e.g. 1.9%+2)  |
             +---------------------+---------------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
         v                                                   v
+------------------+                               +--------------------+
| Ground-Truth     |                               | Exception Matrix   |
| Evaluator        |                               | & Settlement Q&A   |
+------------------+                               +--------------------+
```

---

## Project Structure

```
ledgermatch-ai/
├── backend/
│   ├── main.py              # FastAPI application endpoints and static file serving
│   ├── pipeline.py          # Orchestration pipeline for multi-pass matching
│   ├── matcher.py           # Exact and fuzzy matching logic
│   ├── gateway_matcher.py   # Three-way gateway reconciliation module
│   ├── llm_agent.py         # LLM agent for ambiguous transaction pair resolution
│   ├── llm_provider.py      # LLM provider wrapper (Groq SDK + mock fallback)
│   ├── qa_agent.py          # Run-grounded conversational Q&A agent
│   ├── data_generator.py    # Synthetic multi-source dataset and ground truth generator
│   ├── evaluator.py         # Ground-truth accuracy and trap-case evaluation metrics
│   ├── requirements.txt     # Python backend dependencies
│   ├── .env.example         # Template for environment variables
│   └── .env                 # Environment configuration (API keys)
├── frontend/
│   ├── src/
│   │   ├── components/      # Modular UI components (Tables, Charts, Panels, Hero)
│   │   ├── api.js           # REST client for backend API communication
│   │   ├── currency.js      # Multi-currency formatting utilities
│   │   ├── csvExport.js     # Client-side reconciliation report exporter
│   │   ├── App.jsx          # Root application component
│   │   ├── main.jsx         # React application entry point
│   │   └── index.css        # Tailwind CSS styling and theme definitions
│   ├── package.json         # Node.js dependencies and scripts
│   ├── vite.config.js       # Vite configuration with API proxy
│   └── index.html           # HTML template
└── sample_data/             # Pre-generated test CSV files for inspection
    ├── internal_ledger.csv
    ├── bank_settlements.csv
    ├── gateway_settlements.csv
    └── answer_key.csv
```

---

## Setup & Installation

### Prerequisites

- **Python**: Version 3.11 or higher
- **Node.js**: Version 18 or higher
- **Package Managers**: `pip` and `npm`

---

### 1. Backend Setup

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     python -m venv venv
     .\venv\Scripts\activate.bat
     ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

---

### 2. Groq Cloud API Key Configuration

LedgerMatch AI supports live LLM execution via Groq Cloud (`llama-3.3-70b-versatile`). If no API key is provided, the application automatically falls back to an offline heuristic mock mode without crashing.

1. Obtain a free API key from the [Groq Cloud Console](https://console.groq.com/keys).
2. Copy the sample environment file to `.env` in the `backend/` folder:
   - **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```
   - **Windows**:
     ```powershell
     copy .env.example .env
     ```
3. Open `backend/.env` and add your API key:
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   ```

---

### 3. Frontend Setup

1. In a separate terminal, navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Build the frontend distribution bundle (for production serving via FastAPI):
   ```bash
   npm run build
   ```

---

## Running the Application

### Option A: Unified Mode (FastAPI serves built frontend)

1. Make sure you built the frontend using `npm run build` in the `frontend` folder.
2. In the `backend` directory (with virtual environment activated):
   ```bash
   uvicorn main:app --port 8000
   ```
3. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

---

### Option B: Development Mode (Hot Reload)

1. **Terminal 1 (Backend)**:
   ```bash
   cd backend
   # Activate virtual environment first
   uvicorn main:app --reload --port 8000
   ```

2. **Terminal 2 (Frontend)**:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```
   *(Vite automatically proxies `/api/*` requests to FastAPI on port 8000).*

---

## Custom CSV Schema Requirements

When using the **"Use my own CSVs"** upload feature, ensure your files include the following headers:

### Internal Ledger (`internal_file`)
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `internal_id` | String | Unique transaction ID (e.g., `TXN1001`) |
| `date` | Date (`YYYY-MM-DD`) | Transaction initiation date |
| `merchant_name` | String | Recorded counterparty or vendor name |
| `amount` | Float | Transaction gross amount |
| `reference` | String | External payment reference or invoice ID |

### Bank Settlement File (`bank_file`)
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `bank_id` | String | Bank statement line item ID (e.g., `STL5001`) |
| `value_date` | Date (`YYYY-MM-DD`) | Value/settlement date |
| `narration` | String | Bank transaction narration / payee text |
| `settled_amount` | Float | Net amount received in bank |
| `reference` | String | Bank reference number (if available) |

---

## API Reference

| Endpoint | Method | Parameters / Body | Description |
| :--- | :---: | :--- | :--- |
| `/api/reconcile/sample` | `POST` | `n_records: int` (default: 60)<br>`seed: int` (optional) | Generates synthetic datasets, executes 3-pass reconciliation + gateway cross-check, and computes evaluation metrics. |
| `/api/reconcile/upload` | `POST` | `multipart/form-data`<br>`internal_file`, `bank_file` | Runs reconciliation on user-uploaded internal and bank CSV files. |
| `/api/ask` | `POST` | `{"question": string, "result_context": object}` | Queries the Settlement Q&A agent grounded strictly in current batch data. |
| `/api/health` | `GET` | None | Returns backend status, LLM runtime mode (`live` vs `mock`), and active provider. |

---

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pandas, RapidFuzz, Faker, Groq SDK, Pydantic
- **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide Icons
- **Inference**: Groq Cloud API (`openai/gpt-oss-20b` / `llama-3.3-70b-versatile`) with offline fallback
