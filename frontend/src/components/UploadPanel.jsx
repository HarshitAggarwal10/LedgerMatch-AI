import { useState } from "react";

export default function UploadPanel({ onRunUpload, running }) {
  const [internalFile, setInternalFile] = useState(null);
  const [bankFile, setBankFile] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = () => {
    if (!internalFile || !bankFile) {
      setError("Please choose both files first.");
      return;
    }
    setError(null);
    onRunUpload(internalFile, bankFile).then((err) => {
      if (err) setError(err);
    });
  };

  return (
    <section className="border-y border-border-soft bg-bg-card">
      <div className="mx-auto max-w-6xl px-8 py-10">
        <h2 className="font-display text-2xl font-normal">Reconcile your own files</h2>
        <p className="mt-2 text-sm text-text-secondary">
          Internal ledger needs columns: <code>internal_id, date, merchant_name, amount, reference</code>.
          <br />
          Bank file needs: <code>bank_id, value_date, narration, settled_amount, reference</code>.
        </p>

        <div className="mt-6 flex flex-wrap gap-4">
          <FileDrop label="Internal ledger CSV" file={internalFile} onChange={setInternalFile} />
          <FileDrop label="Bank settlement CSV" file={bankFile} onChange={setBankFile} />
        </div>

        <button
          onClick={handleRun}
          disabled={running}
          className="mt-6 rounded-lg bg-text-primary px-6 py-3 font-semibold text-[#17140f] transition hover:bg-accent-bright disabled:cursor-not-allowed disabled:opacity-50"
        >
          {running ? "Reconciling…" : "Reconcile these files"}
        </button>

        {error && (
          <pre className="mt-4 whitespace-pre-wrap rounded-lg border border-danger bg-danger/10 p-4 text-sm text-danger">
            {error}
          </pre>
        )}
      </div>
    </section>
  );
}

function FileDrop({ label, file, onChange }) {
  return (
    <label className="flex min-w-[240px] flex-1 cursor-pointer flex-col items-center gap-1 rounded-lg border border-dashed border-border p-6 text-center text-sm text-text-secondary transition hover:border-accent hover:text-text-primary">
      <span>{file ? file.name : label}</span>
      <input
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => onChange(e.target.files[0] || null)}
      />
    </label>
  );
}
