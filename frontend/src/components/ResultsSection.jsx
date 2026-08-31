import { useState } from "react";
import StatsGrid from "./StatsGrid";
import MatchedTable from "./MatchedTable";
import ExceptionsTable from "./ExceptionsTable";
import GatewaySection from "./GatewaySection";
import QAPanel from "./QAPanel";
import TrapSpotlight from "./TrapSpotlight";
import PipelineProgress from "./PipelineProgress";
import ConfidenceExplorer from "./ConfidenceExplorer";
import { downloadCsv } from "../csvExport";

export default function ResultsSection({ loading, loadingText, result, currency }) {
  const [explainQuestion, setExplainQuestion] = useState(null);

  return (
    <section id="run" className="mx-auto max-w-6xl px-8 py-16">
      {loading && <PipelineProgress loadingText={loadingText} />}

      {!loading && result && (
        <>
          {result.seed_used !== undefined && result.seed_used !== null && (
            <p className="mb-4 font-mono text-[0.72rem] text-text-muted">
              Reproducible run — seed={result.seed_used}
            </p>
          )}
          <TrapSpotlight trapCase={result.scoring?.trap_case} />

          <StatsGrid data={result} />

          <ConfidenceExplorer data={result} />

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <MatchedTable data={result} currency={currency} />
            <ExceptionsTable
              exceptions={result.exceptions}
              currency={currency}
              onExplain={(id) =>
                setExplainQuestion({ text: `Why didn't ${id} match?`, nonce: Date.now() })
              }
            />
          </div>

          <div className="mt-8">
            <button
              onClick={() => downloadCsv(result)}
              className="rounded-lg border border-border px-5 py-2.5 text-sm font-semibold transition hover:border-accent hover:text-accent-bright"
            >
              Download full report (CSV)
            </button>
          </div>

          <GatewaySection gatewayReconciliation={result.gateway_reconciliation} currency={currency} />
          <QAPanel result={result} externalQuestion={explainQuestion} />
        </>
      )}
    </section>
  );
}