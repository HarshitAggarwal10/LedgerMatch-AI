const NODES = [
  { title: "CSV uploads", sub: "or synthetic batch" },
  { title: "Exact matcher", sub: "pandas" },
  { title: "Fuzzy matcher", sub: "rapidfuzz" },
  { title: "LLM agent", sub: "Groq API", highlight: true },
  { title: "Gateway cross-check", sub: "3rd source" },
  { title: "Scored report", sub: "FastAPI JSON" },
];

export default function Architecture() {
  return (
    <section id="architecture" className="mx-auto max-w-6xl border-t border-border-soft px-8 py-20">
      <p className="mb-2 font-mono text-xs uppercase tracking-widest text-accent">Architecture</p>
      <h2 className="font-display text-3xl font-normal">What runs where</h2>
      <div className="mt-10 flex flex-wrap items-center gap-3">
        {NODES.map((n, i) => (
          <div key={n.title} className="contents">
            <div
              className={`min-w-[140px] rounded-lg border p-4 text-center text-sm ${
                n.highlight ? "border-accent text-accent-bright" : "border-border bg-bg-card"
              }`}
            >
              {n.title}
              <span className="mt-1 block font-mono text-[0.7rem] text-text-muted">{n.sub}</span>
            </div>
            {i < NODES.length - 1 && <span className="text-lg text-text-muted">→</span>}
          </div>
        ))}
      </div>
    </section>
  );
}
