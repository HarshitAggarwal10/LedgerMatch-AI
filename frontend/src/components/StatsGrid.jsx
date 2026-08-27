function StatCard({ label, value, note, danger }) {
  return (
    <div
      className={`flex flex-col gap-1 rounded-xl border p-5 ${
        danger ? "border-danger/35 bg-bg-card" : "border-border bg-bg-card"
      }`}
    >
      <span className="font-mono text-[0.68rem] uppercase tracking-wide text-text-muted">
        {label}
      </span>
      <span className={`font-display text-3xl ${danger ? "text-danger" : "text-text-primary"}`}>
        {value}
      </span>
      {note && <span className="text-[0.78rem] text-text-secondary">{note}</span>}
    </div>
  );
}

export default function StatsGrid({ data }) {
  const { scoring, exact_matches, fuzzy_matches, llm_matches, exceptions, performance } = data;

  const llmMode = llm_matches[0]?.llm_mode === "live" ? "via Claude API" : "via mock mode";

  return (
    <div className="mb-10 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
      <StatCard
        label="Match rate"
        value={scoring ? `${scoring.match_rate_pct}%` : "—"}
        note={scoring ? `${scoring.correct_matches} of ${scoring.total_true_matches} true matches` : "no ground truth"}
      />
      <StatCard
        label="Auto-matched"
        value={exact_matches.length + fuzzy_matches.length}
        note="exact + fuzzy, no LLM needed"
      />
      <StatCard
        label="Resolved by agent"
        value={llm_matches.length}
        note={llm_matches.length ? llmMode : "—"}
      />
      <StatCard
        label="False-match rate"
        value={scoring ? `${scoring.false_match_rate_pct}%` : "—"}
        note="wrongly matched pairs"
        danger
      />
      <StatCard
        label="Exceptions"
        value={exceptions.length}
        note="unresolved, not hidden"
      />
      <StatCard
        label="Throughput"
        value={performance ? `${performance.records_per_second}/s` : "—"}
        note={performance ? `${performance.total_records_processed} records in ${performance.elapsed_seconds}s` : ""}
      />
    </div>
  );
}
