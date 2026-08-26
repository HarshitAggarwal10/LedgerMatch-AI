function csvEscape(val) {
  const s = String(val ?? "");
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function downloadCsv(result) {
  const rows = [["side_or_method", "internal_id", "bank_id", "merchant_name", "amount", "confidence_or_reason"]];

  for (const m of result.exact_matches) rows.push(["exact", m.internal_id, m.bank_id, m.merchant_name, m.amount, `${m.confidence}%`]);
  for (const m of result.fuzzy_matches) rows.push(["fuzzy", m.internal_id, m.bank_id, m.merchant_name, m.amount, `${m.confidence}%`]);
  for (const m of result.llm_matches) rows.push(["agent", m.internal_id, m.bank_id, m.merchant_name, m.amount, `${m.llm_confidence}%`]);
  for (const e of result.exceptions) rows.push([`exception_${e.side}`, e.id, "", e.merchant_name, e.amount, e.reason]);

  const csv = rows.map((r) => r.map(csvEscape).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "ledgermatch_report.csv";
  a.click();
  URL.revokeObjectURL(url);
}
