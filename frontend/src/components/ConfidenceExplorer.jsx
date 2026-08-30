import { useMemo, useState } from "react";

const BUCKETS = [
  { label: "<60", min: 0, max: 60 },
  { label: "60-69", min: 60, max: 70 },
  { label: "70-79", min: 70, max: 80 },
  { label: "80-89", min: 80, max: 90 },
  { label: "90-99", min: 90, max: 100 },
  { label: "100", min: 100, max: 101 },
];

const BUILT_IN_THRESHOLD = 90; // matches FUZZY_AUTO_THRESHOLD in backend/matcher.py

export default function ConfidenceExplorer({ data }) {
  const { exact_matches, fuzzy_matches, llm_matches, scoring } = data;
  const [threshold, setThreshold] = useState(BUILT_IN_THRESHOLD);

  const scorable = useMemo(() => {
    // Fuzzy + agent matches only -- exact matches carry no meaningful
    // "confidence" tradeoff since they're identical on reference+amount.
    const fuzzy = fuzzy_matches.map((m) => ({ ...m, confidence: m.confidence, source: "fuzzy" }));
    const agent = llm_matches.map((m) => ({ ...m, confidence: m.llm_confidence, source: "agent" }));
    return [...fuzzy, ...agent];
  }, [fuzzy_matches, llm_matches]);

  const falseKeySet = useMemo(() => {
    if (!scoring) return null;
    return new Set(scoring.false_matches.map((f) => `${f.internal_id}|${f.bank_id}`));
  }, [scoring]);

  const histogram = useMemo(() => {
    const all = [...exact_matches.map(() => 100), ...scorable.map((m) => m.confidence)];
    return BUCKETS.map((b) => ({
      ...b,
      count: all.filter((c) => c >= b.min && c < b.max).length,
    }));
  }, [exact_matches, scorable]);

  const maxBucketCount = Math.max(1, ...histogram.map((b) => b.count));

  const simulated = useMemo(() => {
    const kept = scorable.filter((m) => m.confidence >= threshold);
    const heldBack = scorable.length - kept.length;
    const totalMatched = exact_matches.length + kept.length;

    if (!scoring) {
      return { totalMatched, heldBack, matchRate: null, falseMatchRate: null };
    }

    const falseCount = kept.filter((m) => falseKeySet.has(`${m.internal_id}|${m.bank_id}`)).length;
    const correctCount = exact_matches.length + kept.length - falseCount;
    const matchRate = scoring.total_true_matches
      ? round1((100 * correctCount) / scoring.total_true_matches)
      : 0;
    const falseMatchRate = totalMatched ? round1((100 * falseCount) / totalMatched) : 0;

    return { totalMatched, heldBack, matchRate, falseMatchRate };
  }, [scorable, threshold, exact_matches.length, scoring, falseKeySet]);

  return (
    <div className="mb-10 rounded-xl border border-border bg-bg-card p-6">
      <p className="mb-1 font-mono text-xs uppercase tracking-widest text-accent">
        Explore the tradeoff
      </p>
      <h3 className="font-display text-xl font-normal">Confidence threshold &amp; distribution</h3>
      <p className="mt-2 max-w-[70ch] text-sm text-text-secondary">
        This run auto-matched anything scoring {BUILT_IN_THRESHOLD}%+ confident. Drag the
        threshold to see the tradeoff: a stricter cutoff catches fewer false matches but
        pushes more records to manual review; a looser one auto-resolves more but risks
        more mistakes.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_1.2fr]">
        {/* Histogram */}
        <div>
          <p className="mb-2 text-[0.78rem] text-text-muted">Confidence distribution (all matched records)</p>
          <div className="flex h-32 items-end gap-2">
            {histogram.map((b) => (
              <div key={b.label} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
                <div
                  className={`w-full rounded-t transition-all ${
                    b.min >= threshold ? "bg-accent" : "bg-border"
                  }`}
                  style={{ height: `${Math.max(4, (b.count / maxBucketCount) * 112)}px` }}
                  title={`${b.count} records`}
                />
                <span className="font-mono text-[0.62rem] text-text-muted">{b.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Slider + live recompute */}
        <div>
          <div className="flex items-center justify-between text-[0.78rem] text-text-secondary">
            <span>Confidence threshold</span>
            <span className="font-mono text-accent-bright">{threshold}%</span>
          </div>
          <input
            type="range"
            min={50}
            max={100}
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="mt-2 w-full accent-accent"
          />
          <div className="mt-1 flex justify-between font-mono text-[0.62rem] text-text-muted">
            <span>50%</span>
            <span>built-in: {BUILT_IN_THRESHOLD}%</span>
            <span>100%</span>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3">
            <MiniStat
              label="Simulated match rate"
              value={simulated.matchRate !== null ? `${simulated.matchRate}%` : "—"}
              note={simulated.matchRate === null ? "no ground truth" : undefined}
            />
            <MiniStat
              label="Simulated false-match rate"
              value={simulated.falseMatchRate !== null ? `${simulated.falseMatchRate}%` : "—"}
              danger
            />
            <MiniStat label="Auto-matched at this threshold" value={simulated.totalMatched} />
            <MiniStat label="Held back for review" value={simulated.heldBack} />
          </div>
        </div>
      </div>
    </div>
  );
}

function round1(n) {
  return Math.round(n * 10) / 10;
}

function MiniStat({ label, value, note, danger }) {
  return (
    <div className="rounded-lg border border-border-soft bg-bg px-3 py-2">
      <div className="font-mono text-[0.62rem] uppercase tracking-wide text-text-muted">{label}</div>
      <div className={`font-display text-lg ${danger ? "text-danger" : "text-text-primary"}`}>{value}</div>
      {note && <div className="text-[0.68rem] text-text-muted">{note}</div>}
    </div>
  );
}
