const methodStyle = {
  exact: "text-success border-success/40",
  fuzzy: "text-accent border-accent/40",
  agent: "text-accent-bright border-accent-bright/50",
};

function formatAmount(n) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function MatchedTable({ data }) {
  const rows = [
    ...data.exact_matches.map((m) => ({ ...m, method: "exact" })),
    ...data.fuzzy_matches.map((m) => ({ ...m, method: "fuzzy" })),
    ...data.llm_matches.map((m) => ({ ...m, method: "agent", confidence: m.llm_confidence })),
  ];

  return (
    <div>
      <h3 className="flex items-center gap-2 font-display text-xl font-normal">
        Matched records
        <span className="rounded-full bg-border-soft px-2 py-0.5 font-mono text-xs text-text-secondary">
          {rows.length}
        </span>
      </h3>
      <p className="mt-1 text-sm text-text-secondary">
        Exact matches, auto-fuzzy matches, and pairs the agent confirmed.
      </p>

      <div className="thin-scroll mt-3 max-h-[420px] overflow-auto rounded-lg border border-border">
        <table className="w-full border-collapse text-[0.82rem]">
          <thead>
            <tr>
              {["Internal", "Bank", "Merchant", "Amount", "Method", "Confidence"].map((h) => (
                <th
                  key={h}
                  className="sticky top-0 border-b border-border bg-bg-card px-3 py-2 text-left font-mono text-[0.68rem] uppercase tracking-wide text-text-muted"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={6} className="px-3 py-4 text-text-secondary">No matches yet.</td></tr>
            ) : (
              rows.map((r, i) => (
                <tr key={i} className="border-b border-border-soft last:border-none hover:bg-bg-card-hover">
                  <td className="px-3 py-2 font-mono text-text-secondary">{r.internal_id}</td>
                  <td className="px-3 py-2 font-mono text-text-secondary">{r.bank_id}</td>
                  <td className="px-3 py-2 font-mono text-text-secondary">{r.merchant_name}</td>
                  <td className="px-3 py-2 font-mono text-text-secondary">₹{formatAmount(r.amount)}</td>
                  <td className="px-3 py-2">
                    <span className={`rounded border px-1.5 py-0.5 font-mono text-[0.7rem] ${methodStyle[r.method]}`}>
                      {r.method}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-text-secondary">{r.confidence}%</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
