import { useState, useEffect, useRef } from "react";
import { askQuestion } from "../api";

const SUGGESTIONS = [
  "How much money is still unreconciled?",
  "Which exceptions are worth checking first?",
  "Summarize this run in two sentences.",
];

export default function QAPanel({ result, externalQuestion }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [asking, setAsking] = useState(false);
  const panelRef = useRef(null);
  const lastExternalRef = useRef(null);

  const send = async (question) => {
    if (!question.trim() || asking) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setAsking(true);
    try {
      const res = await askQuestion(question, result);
      setMessages((m) => [...m, { role: "agent", text: res.answer, mode: res.mode, provider: res.provider }]);
    } catch {
      setMessages((m) => [...m, { role: "agent", text: "Couldn't reach the backend for that one.", mode: "error" }]);
    } finally {
      setAsking(false);
    }
  };

  // When a row's "Explain →" button fires a question up from ExceptionsTable,
  // scroll the panel into view and send it automatically.
  useEffect(() => {
    if (externalQuestion && externalQuestion.nonce !== lastExternalRef.current) {
      lastExternalRef.current = externalQuestion.nonce;
      panelRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      send(externalQuestion.text);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalQuestion]);

  return (
    <div ref={panelRef} className="mt-14 rounded-xl border border-border bg-bg-card p-6">
      <p className="mb-1 font-mono text-xs uppercase tracking-widest text-accent">
        Settlement Q&amp;A agent
      </p>
      <h3 className="font-display text-2xl font-normal">Ask about this run</h3>
      <p className="mt-2 text-sm text-text-secondary">
        Answers are grounded in the actual JSON from the reconciliation above —
        not general knowledge — so it can't invent a number that isn't really there.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => send(s)}
            disabled={asking}
            className="rounded-full border border-border px-3 py-1.5 text-xs text-text-secondary transition hover:border-accent hover:text-accent-bright disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="mt-4 flex max-h-72 flex-col gap-3 overflow-auto thin-scroll">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-lg px-4 py-2.5 text-sm ${
              m.role === "user"
                ? "self-end bg-text-primary text-[#17140f]"
                : "self-start border border-border bg-bg text-text-secondary"
            }`}
          >
            {m.text}
            {m.role === "agent" && m.mode === "mock" && (
              <span className="mt-1 block font-mono text-[0.65rem] text-accent">(mock mode)</span>
            )}
            {m.role === "agent" && m.mode === "live" && m.provider && (
              <span className="mt-1 block font-mono text-[0.65rem] text-success">via {m.provider}</span>
            )}
          </div>
        ))}
        {asking && (
          <div className="self-start rounded-lg border border-border bg-bg px-4 py-2.5 text-sm text-text-muted">
            thinking…
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="mt-4 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about this reconciliation…"
          className="flex-1 rounded-lg border border-border bg-bg px-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
        />
        <button
          type="submit"
          disabled={asking}
          className="rounded-lg bg-text-primary px-5 py-2.5 text-sm font-semibold text-[#17140f] transition hover:bg-accent-bright disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
