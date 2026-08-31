import { useEffect, useState } from "react";
import Header from "./components/Header";
import Hero from "./components/Hero";
import UploadPanel from "./components/UploadPanel";
import ResultsSection from "./components/ResultsSection";
import PipelineSteps from "./components/PipelineSteps";
import Architecture from "./components/Architecture";
import Footer from "./components/Footer";
import { fetchHealth, reconcileSample, reconcileUpload } from "./api";

export default function App() {
  const [llmMode, setLlmMode] = useState(null);
  const [provider, setProvider] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");
  const [result, setResult] = useState(null);
  const [seed, setSeed] = useState("");

  useEffect(() => {
    fetchHealth()
      .then((h) => {
        setLlmMode(h.llm_mode);
        setProvider(h.provider);
      })
      .catch(() => setLlmMode(null));
  }, []);

  const runSample = async () => {
    setLoading(true);
    setLoadingText("Generating a fresh synthetic batch…");
    document.getElementById("run")?.scrollIntoView({ behavior: "smooth" });
    try {
      // Race against a minimum display time so the pipeline-stage animation
      // is actually visible -- the backend itself typically responds in
      // single-digit milliseconds, which would otherwise make the staged
      // reveal flash by unseen. Purely a UX pacing choice; no data shown
      // during this window is fabricated -- it's generic stage labels only.
      const [data] = await Promise.all([
        reconcileSample(60, seed || null),
        new Promise((r) => setTimeout(r, 1400)),
      ]);
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  const runUpload = async (internalFile, bankFile) => {
    setLoading(true);
    setLoadingText("Reconciling your files…");
    document.getElementById("run")?.scrollIntoView({ behavior: "smooth" });
    try {
      const [data] = await Promise.all([
        reconcileUpload(internalFile, bankFile),
        new Promise((r) => setTimeout(r, 1400)),
      ]);
      if (data.error) {
        setLoading(false);
        return (
          `${data.error}\n\n` +
          `Missing internal columns: ${data.missing_internal_columns?.join(", ") || "none"}\n` +
          `Missing bank columns: ${data.missing_bank_columns?.join(", ") || "none"}\n\n` +
          `Expected internal columns: ${data.expected_internal_columns?.join(", ")}\n` +
          `Expected bank columns: ${data.expected_bank_columns?.join(", ")}`
        );
      }
      setResult(data);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg text-text-primary">
      <Header llmMode={llmMode} provider={provider} />
      <main>
        <Hero
          onRunSample={runSample}
          onShowUpload={() => setShowUpload(true)}
          running={loading}
          seed={seed}
          onSeedChange={setSeed}
        />
        {showUpload && <UploadPanel onRunUpload={runUpload} running={loading} />}
        {(loading || result) && (
          <ResultsSection loading={loading} loadingText={loadingText} result={result} />
        )}
        <PipelineSteps />
        <Architecture />
      </main>
      <Footer />
    </div>
  );
}
