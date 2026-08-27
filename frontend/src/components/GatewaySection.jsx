function formatAmount(n) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function GatewaySection({ gatewayReconciliation }) {
  if (!gatewayReconciliation) return null;

  const { full_match, partial_match, gateway_only } = gatewayReconciliation;
  const total = full_match.length + partial_match.length + gateway_only.length;

  return (
    <div className="mt-14">
      <p className="mb-2 font-mono text-xs uppercase tracking-widest text-accent">
        Third source
      </p>
      <h3 className="font-display text-2xl font-normal">
        Bringing in the payment gateway
      </h3>
      <p className="mt-2 max-w-[70ch] text-sm text-text-secondary">
        A two-file diff only proves your books agree with the bank. LedgerMatch
        also checks the payment gateway's own settlement report — the third
        independent record of the same money movement — so a mismatch that
        happens to slip past both other sources doesn't go unnoticed.
      </p>

      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <GatewayStat
          label="Full three-way match"
          value={full_match.length}
          total={total}
          tone="success"
        />
        <GatewayStat
          label="Partial (2 of 3 agree)"
          value={partial_match.length}
          total={total}
          tone="accent"
        />
        <GatewayStat
          label="Gateway-only"
          value={gateway_only.length}
          total={total}
          tone="danger"
        />
      </div>

      {partial_match.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-text-primary">
            Partial matches worth a look
          </h4>
          <div className="thin-scroll mt-2 max-h-64 overflow-auto rounded-lg border border-border">
            <table className="w-full border-collapse text-[0.8rem]">
              <thead>
                <tr>
                  {["Internal", "Merchant", "Amount", "Note"].map((h) => (
                    <th key={h} className="sticky top-0 border-b border-border bg-bg-card px-3 py-2 text-left font-mono text-[0.65rem] uppercase tracking-wide text-text-muted">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {partial_match.map((p, i) => (
                  <tr key={i} className="border-b border-border-soft last:border-none hover:bg-bg-card-hover">
                    <td className="px-3 py-2 font-mono text-text-secondary">{p.internal_id}</td>
                    <td className="px-3 py-2 font-mono text-text-secondary">{p.merchant_name}</td>
                    <td className="px-3 py-2 font-mono text-text-secondary">₹{formatAmount(p.amount)}</td>
                    <td className="px-3 py-2 text-text-secondary">{p.gateway_note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

const toneClasses = {
  success: "text-success",
  accent: "text-accent",
  danger: "text-danger",
};

function GatewayStat({ label, value, total, tone }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="rounded-xl border border-border bg-bg-card p-5">
      <span className="font-mono text-[0.68rem] uppercase tracking-wide text-text-muted">{label}</span>
      <div className={`mt-1 font-display text-2xl ${toneClasses[tone]}`}>{value}</div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-border-soft">
        <div className={`h-full ${tone === "success" ? "bg-success" : tone === "accent" ? "bg-accent" : "bg-danger"}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
