export default function TrapSpotlight({ trapCase }) {
  if (!trapCase) return null;

  const { was_fooled, bank_id, matched_internal_id } = trapCase;

  return (
    <div
      className={`mb-8 flex items-start gap-4 rounded-xl border p-5 ${
        was_fooled ? "border-danger/50 bg-danger/5" : "border-success/40 bg-success/5"
      }`}
    >
      <span className="mt-0.5 text-xl">{was_fooled ? "⚠" : "✓"}</span>
      <div>
        <p className="font-mono text-[0.68rem] uppercase tracking-wide text-text-muted">
          Built-in trap case
        </p>
        <p className="mt-1 text-sm text-text-primary">
          Every run includes one deliberate <strong>lookalike</strong> — a bank record
          ({bank_id}) engineered to superficially resemble a real transaction (same
          merchant, close-but-wrong amount) with no genuine internal counterpart at all.
        </p>
        <p className={`mt-1.5 text-sm font-semibold ${was_fooled ? "text-danger" : "text-success"}`}>
          {was_fooled
            ? `This run got fooled — it was wrongly matched to ${matched_internal_id}.`
            : "This run correctly refused to match it and left it as an exception."}
        </p>
      </div>
    </div>
  );
}
