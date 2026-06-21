import { Variant } from "../types";
import { ScoreBar } from "./ScoreBar";

interface Props {
  bestVariant: Variant | null;
}

export function ResultsPanel({ bestVariant }: Props) {
  if (!bestVariant) return null;

  return (
    <div className="bg-surface rounded-lg border border-border-color p-5">
      <h2 className="text-primary font-sans font-semibold text-base mb-4">
        Best Result
      </h2>
      <div className="mb-3">
        <ScoreBar label="score" score={bestVariant.score} />
      </div>
      <p className="text-xs text-muted font-mono mb-3 italic">
        {bestVariant.reason}
      </p>
      <div className="bg-elevated rounded border border-border-color p-3 mb-3">
        <p className="text-xs text-muted mb-1 font-mono">Output</p>
        <pre className="text-sm text-primary font-mono whitespace-pre-wrap leading-relaxed">
          {bestVariant.output}
        </pre>
      </div>
      <button
        onClick={() => navigator.clipboard.writeText(bestVariant.prompt)}
        className="text-xs font-mono text-accent-teal border border-accent-teal rounded px-3 py-1 hover:bg-accent-teal hover:text-base transition-colors"
      >
        Copy prompt
      </button>
    </div>
  );
}
