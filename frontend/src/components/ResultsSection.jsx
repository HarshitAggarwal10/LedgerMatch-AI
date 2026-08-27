import StatsGrid from "./StatsGrid";
import MatchedTable from "./MatchedTable";
import ExceptionsTable from "./ExceptionsTable";
import GatewaySection from "./GatewaySection";
import QAPanel from "./QAPanel";
import { downloadCsv } from "../csvExport";

export default function ResultsSection({ loading, loadingText, result }) {
  return (
    <section id="run" className="mx-auto max-w-6xl px-8 py-16">
      {loading && (
        <div className="flex flex-col items-center gap-4 py-20 text-text-secondary">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
          <p>{loadingText}</p>
        </div>
      )}

      {!loading && result && (
        <>
          <StatsGrid data={result} />

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <MatchedTable data={result} />
            <ExceptionsTable exceptions={result.exceptions} />
          </div>

          <div className="mt-8">
            <button
              onClick={() => downloadCsv(result)}
              className="rounded-lg border border-border px-5 py-2.5 text-sm font-semibold transition hover:border-accent hover:text-accent-bright"
            >
              Download full report (CSV)
            </button>
          </div>

          <GatewaySection gatewayReconciliation={result.gateway_reconciliation} />
          <QAPanel result={result} />
        </>
      )}
    </section>
  );
}
