import { useState, Fragment } from "react";
import { formatAmount } from "../currency";

const methodStyle = {
  exact: "text-success border-success/40",
  fuzzy: "text-accent border-accent/40",
  agent: "text-accent-bright border-accent-bright/50",
};

export default function MatchedTable({ data, currency }) {
  const [expandedIdx, setExpandedIdx] = useState(null);

  const rows = [
    ...data.exact_matches.map((m) => ({ ...m, method: "exact" })),
    ...data.fuzzy_matches.map((m) => ({ ...m, method: "fuzzy" })),
    ...data.llm_matches.map((m) => ({
      ...m,
      method: "agent",
      confidence: m.llm_confidence,
      reason: `[${m.llm_mode === "live" ? m.provider || "live agent" : "mock mode"}] ${m.llm_reason}`,
    })),
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
        <span className="text-text-muted"> Click a row to see why.</span>
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
                <Fragment key={i}>
                  <tr
                    onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                    className="cursor-pointer border-b border-border-soft last:border-none hover:bg-bg-card-hover"
                  >
                    <td className="px-3 py-2 font-mono text-text-secondary">{r.internal_id}</td>
                    <td className="px-3 py-2 font-mono text-text-secondary">{r.bank_id}</td>
                    <td className="px-3 py-2 font-mono text-text-secondary">{r.merchant_name}</td>
                    <td className="px-3 py-2 font-mono text-text-secondary">{formatAmount(r.amount, currency)}</td>
                    <td className="px-3 py-2">
                      <span className={`rounded border px-1.5 py-0.5 font-mono text-[0.7rem] ${methodStyle[r.method]}`}>
                        {r.method}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-text-secondary">
                      {r.confidence}% <span className="ml-1 text-text-muted">{expandedIdx === i ? "▲" : "▼"}</span>
                    </td>
                  </tr>
                  {expandedIdx === i && (
                    <tr className="border-b border-border-soft bg-bg">
                      <td colSpan={6} className="px-3 py-3 text-[0.8rem] text-text-secondary">
                        <span className="font-mono text-[0.68rem] uppercase tracking-wide text-accent">Why this matched: </span>
                        {r.reason || "No detailed reason recorded for this match."}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}