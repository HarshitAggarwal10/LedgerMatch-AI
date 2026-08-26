export default function Header({ llmMode }) {
  const isLive = llmMode === "live";
  const label = llmMode
    ? isLive
      ? "● agent: live (Claude API)"
      : "● agent: mock mode (no API key set)"
    : "checking mode…";

  return (
    <header className="sticky top-0 z-50 border-b border-border-soft bg-bg/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-8 px-8 py-4">
        <div className="flex items-baseline gap-2 whitespace-nowrap font-display text-xl">
          <span className="text-accent text-base">◆</span>
          <span>
            LedgerMatch <em className="text-accent-bright not-italic">AI</em>
          </span>
        </div>
        <nav className="hidden gap-7 text-sm text-text-secondary md:flex">
          <a href="#how-it-works" className="hover:text-text-primary">How it works</a>
          <a href="#run" className="hover:text-text-primary">Run reconciliation</a>
          <a href="#architecture" className="hover:text-text-primary">Architecture</a>
        </nav>
        <span
          className={`whitespace-nowrap rounded-full border px-3 py-1 font-mono text-[0.7rem] ${
            isLive
              ? "border-success text-success"
              : "border-accent-dim text-accent"
          }`}
        >
          {label}
        </span>
      </div>
    </header>
  );
}
