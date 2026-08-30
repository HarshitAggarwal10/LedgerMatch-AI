import { useEffect, useState } from "react";

const STAGES = [
  "Running exact match pass (reference + amount)…",
  "Running fuzzy match pass (name + amount/date tolerance)…",
  "Sending ambiguous cases to the LLM agent…",
  "Cross-checking against the payment gateway…",
];

// Purely a loading indicator -- no numbers are shown here, because the real
// per-stage counts aren't known until the backend finishes the whole run.
// Once results land, StatsGrid animates the real numbers counting up.
export default function PipelineProgress({ loadingText }) {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    setStageIndex(0);
    const interval = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, STAGES.length - 1));
    }, 450);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-6 py-20">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
      <p className="text-text-secondary">{loadingText}</p>
      <div className="w-full space-y-2.5">
        {STAGES.map((stage, i) => {
          const done = i < stageIndex;
          const active = i === stageIndex;
          return (
            <div
              key={stage}
              className={`flex items-center gap-3 rounded-lg border px-4 py-2.5 text-sm transition-colors ${
                active
                  ? "border-accent/50 bg-bg-card text-text-primary"
                  : done
                    ? "border-border-soft text-text-secondary"
                    : "border-border-soft text-text-muted"
              }`}
            >
              <span className="w-4 font-mono text-xs">
                {done ? "✓" : active ? "…" : "·"}
              </span>
              {stage}
            </div>
          );
        })}
      </div>
    </div>
  );
}
