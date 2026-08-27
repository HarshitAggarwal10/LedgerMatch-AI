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
  const [showUpload, setShowUpload] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then((h) => setLlmMode(h.llm_mode))
      .catch(() => setLlmMode(null));
  }, []);

  const runSample = async () => {
    setLoading(true);
    setLoadingText("Generating a fresh synthetic batch…");
    document.getElementById("run")?.scrollIntoView({ behavior: "smooth" });
    try {
      const data = await reconcileSample(60);
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
      const data = await reconcileUpload(internalFile, bankFile);
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
      <Header llmMode={llmMode} />
      <main>
        <Hero
          onRunSample={runSample}
          onShowUpload={() => setShowUpload(true)}
          running={loading}
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
