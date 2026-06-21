import { GenerationEvent } from "../types";
import { ScoreBar } from "./ScoreBar";

interface Props {
  events: GenerationEvent[];
  isRunning: boolean;
}

export function EvolutionViewer({ events, isRunning }: Props) {
  const genEvents = events.filter((e) => e.event_type === "generation");
  if (genEvents.length === 0 && !isRunning) return null;

  return (
    <div className="bg-surface rounded-lg border border-border-color p-5">
      <h2 className="text-primary font-sans font-semibold text-base mb-4">
        Evolution Progress
        {isRunning && (
          <span className="ml-2 text-sm text-accent-teal animate-pulse font-mono">
            · running
          </span>
        )}
      </h2>
      <div className="space-y-3">
        {genEvents.map((ev) => {
          const top = ev.variants[0];
          const prev = genEvents[genEvents.indexOf(ev) - 1]?.variants[0];
          return (
            <div
              key={ev.generation}
              className="border border-border-color rounded bg-elevated p-3"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-muted">
                  Gen {ev.generation}
                </span>
                <span className="text-xs font-mono text-accent-teal">
                  best: {top ? (top.score * 100).toFixed(0) : "—"}%
                </span>
              </div>
              {top && (
                <>
                  <ScoreBar
                    label="score"
                    score={top.score}
                    prevScore={prev?.score}
                  />
                  <p className="text-xs text-muted font-mono mt-2 italic leading-relaxed">
                    {top.reason}
                  </p>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
