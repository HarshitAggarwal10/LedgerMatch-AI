const STEPS = [
  { num: "01", title: "Exact match", body: "Reference ID + amount, matched to the paisa. Resolves the bulk of real-world reconciliation instantly." },
  { num: "02", title: "Fuzzy match", body: "Merchant-name similarity plus amount and date tolerance, for records the bank feed wrote slightly differently." },
  { num: "03", title: "Agent review", body: "Whatever's still ambiguous goes to an LLM, which reasons about both records side by side and explains its call." },
  { num: "04", title: "Gateway cross-check", body: "A third, independent source — the payment gateway's settlement file — confirms or flags what the first two agreed on." },
];

export default function PipelineSteps() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl border-t border-border-soft px-8 py-20">
      <p className="mb-2 font-mono text-xs uppercase tracking-widest text-accent">How it works</p>
      <h2 className="font-display text-3xl font-normal">Four passes. Every one explainable.</h2>
      <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((s) => (
          <div key={s.num} className="border-t border-border pt-4">
            <span className="font-mono text-xs text-accent">{s.num}</span>
            <h4 className="mt-2 font-display text-lg font-normal">{s.title}</h4>
            <p className="mt-2 text-sm text-text-secondary">{s.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
