interface ScoreBarProps {
  label: string;
  score: number;
  prevScore?: number;
}

export function ScoreBar({ label, score, prevScore }: ScoreBarProps) {
  const pct = Math.round(score * 100);
  const delta = prevScore !== undefined ? Math.round((score - prevScore) * 100) : null;
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-muted font-mono">{label}</span>
        <span className="font-mono text-primary">
          {pct}%
          {delta !== null && (
            <span className={delta >= 0 ? "text-accent-teal ml-1" : "text-red-400 ml-1"}>
              {delta >= 0 ? `+${delta}` : delta}
            </span>
          )}
        </span>
      </div>
      <div className="h-1.5 bg-elevated rounded-full overflow-hidden">
        <div
          className="h-full bg-accent-teal transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
