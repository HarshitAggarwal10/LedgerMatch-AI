function formatAmount(n) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function ExceptionsTable({ exceptions }) {
  return (
    <div>
      <h3 className="flex items-center gap-2 font-display text-xl font-normal">
        Exceptions
        <span className="rounded-full bg-border-soft px-2 py-0.5 font-mono text-xs text-danger">
          {exceptions.length}
        </span>
      </h3>
      <p className="mt-1 text-sm text-text-secondary">
        Every unresolved record, with a plain-English reason — nothing swept under the rug.
      </p>

      <div className="thin-scroll mt-3 max-h-[420px] overflow-auto rounded-lg border border-border">
        <table className="w-full border-collapse text-[0.82rem]">
          <thead>
            <tr>
              {["Side", "ID", "Merchant", "Amount", "Reason"].map((h) => (
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
            {exceptions.length === 0 ? (
              <tr><td colSpan={5} className="px-3 py-4 text-text-secondary">No exceptions — everything resolved.</td></tr>
            ) : (
              exceptions.map((e, i) => (
                <tr key={i} className="border-b border-border-soft last:border-none hover:bg-bg-card-hover">
                  <td className="px-3 py-2 font-mono text-text-secondary">{e.side}</td>
                  <td className="px-3 py-2 font-mono text-text-secondary">{e.id}</td>
                  <td className="px-3 py-2 font-mono text-text-secondary">{e.merchant_name}</td>
                  <td className="px-3 py-2 font-mono text-text-secondary">₹{formatAmount(e.amount)}</td>
                  <td className="px-3 py-2 text-text-secondary">{e.reason}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
