// currency.js
// ------------
// LedgerMatch's matching logic (exact/fuzzy matching, amount tolerance,
// date tolerance) never assumed any particular currency or country -- it
// only compares numbers and strings, so a CSV from any business, anywhere,
// already reconciles correctly today. This file just controls how amounts
// are *displayed*, so the UI doesn't default to a currency symbol that
// doesn't match the data you're actually looking at.

export const CURRENCIES = [
  { code: "USD", symbol: "$", label: "USD ($)" },
  { code: "EUR", symbol: "\u20AC", label: "EUR (\u20AC)" },
  { code: "GBP", symbol: "\u00A3", label: "GBP (\u00A3)" },
  { code: "INR", symbol: "\u20B9", label: "INR (\u20B9)" },
  { code: "AED", symbol: "AED ", label: "AED (UAE Dirham)" },
  { code: "SGD", symbol: "S$", label: "SGD (S$)" },
  { code: "AUD", symbol: "A$", label: "AUD (A$)" },
  { code: "JPY", symbol: "\u00A5", label: "JPY (\u00A5)" },
  { code: "NONE", symbol: "", label: "No symbol (plain number)" },
];

export const DEFAULT_CURRENCY = "USD";

export function currencySymbol(code) {
  return CURRENCIES.find((c) => c.code === code)?.symbol ?? "";
}

export function formatAmount(n, currencyCode = DEFAULT_CURRENCY) {
  if (n === null || n === undefined) return "\u2014";
  const formatted = Number(n).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${currencySymbol(currencyCode)}${formatted}`;
}