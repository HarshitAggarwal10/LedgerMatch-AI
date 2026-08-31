const LEDGER_ROWS = [
  { internal: "TXN1000", bank: "STL5000", status: "match", label: "— matched —" },
  { internal: "TXN1001", bank: "STL5001", status: "match", label: "— matched —" },
  { internal: "TXN1013", bank: "STL5013", status: "review", label: "? reviewing ?" },
  { internal: "TXN1042", bank: "—", status: "exception", label: "⚠ exception" },
];

const statusColor = {
  match: "text-success",
  review: "text-accent animate-pulse-soft",
  exception: "text-danger",
};

export default function Hero({ onRunSample, onShowUpload, running, seed, onSeedChange }) {
  return (
    <section className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-8 pb-16 pt-20 md:grid-cols-[1.1fr_0.9fr]">
      <div>
        <p className="mb-3 font-mono text-xs uppercase tracking-widest text-accent">
          AI Finance Controller · Reconciliation Agent
        </p>
        <h1 className="font-display text-5xl leading-[1.08] font-normal md:text-6xl">
          Three ledgers.
          <br />
          One <em className="text-accent-bright not-italic">true</em> answer.
        </h1>
        <p className="mt-5 max-w-[46ch] text-text-secondary text-[1.05rem]">
          LedgerMatch reconciles an internal payment ledger against a bank settlement
          file and a payment gateway report — matching what agrees across all three,
          and explaining, record by record, everything that doesn't. No cherry-picked
          demo runs: every number below is computed live.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <button
            onClick={onRunSample}
            disabled={running}
            className="rounded-lg bg-text-primary px-6 py-3 font-semibold text-[#17140f] transition hover:bg-accent-bright disabled:cursor-not-allowed disabled:opacity-50"
          >
            {running ? "Running…" : "Run on sample batch"}
          </button>
          <button
            onClick={onShowUpload}
            className="rounded-lg border border-border px-6 py-3 font-semibold transition hover:border-accent hover:text-accent-bright"
          >
            Use my own CSVs
          </button>
        </div>

        <div className="mt-3 flex items-center gap-2">
          <label htmlFor="seed-input" className="font-mono text-[0.72rem] text-text-muted">
            seed (optional, for a reproducible run):
          </label>
          <input
            id="seed-input"
            type="number"
            value={seed}
            onChange={(e) => onSeedChange(e.target.value)}
            placeholder="random"
            className="w-24 rounded border border-border bg-bg-card px-2 py-1 font-mono text-[0.72rem] text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
          />
          <button
            type="button"
            onClick={() => onSeedChange("42")}
            className="font-mono text-[0.68rem] text-text-muted underline decoration-dotted hover:text-accent-bright"
          >
            use 42
          </button>
        </div>
      </div>

      <div className="relative overflow-hidden rounded-xl border border-border bg-bg-card p-6">
        <div className="flex flex-col">
          {LEDGER_ROWS.map((row) => (
            <div
              key={row.internal}
              className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 py-2.5 font-mono text-[0.82rem]"
            >
              <span className={row.status === "match" ? "text-text-primary" : "text-text-secondary"}>
                {row.internal}
              </span>
              <span className={`text-center text-[0.68rem] tracking-wide ${statusColor[row.status]}`}>
                {row.label}
              </span>
              <span className={`text-right ${row.status === "match" ? "text-text-primary" : "text-text-secondary"}`}>
                {row.bank}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
