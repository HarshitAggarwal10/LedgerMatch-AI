const BASE = ""; // same-origin: dev server proxies /api, prod is served by FastAPI directly

export async function fetchHealth() {
  const res = await fetch(`${BASE}/api/health`);
  return res.json();
}

export async function reconcileSample(nRecords = 60, seed = null) {
  const params = new URLSearchParams({ n_records: nRecords });
  if (seed !== null && seed !== "") params.set("seed", seed);
  const res = await fetch(`${BASE}/api/reconcile/sample?${params.toString()}`, {
    method: "POST",
  });
  return res.json();
}

export async function reconcileUpload(internalFile, bankFile) {
  const formData = new FormData();
  formData.append("internal_file", internalFile);
  formData.append("bank_file", bankFile);
  const res = await fetch(`${BASE}/api/reconcile/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function askQuestion(question, resultContext) {
  const res = await fetch(`${BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, result_context: resultContext }),
  });
  return res.json();
}
