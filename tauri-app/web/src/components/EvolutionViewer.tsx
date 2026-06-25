import { GenerationEvent } from "../types";
import { ScoreBar } from "./ScoreBar";

interface Props {
  events: GenerationEvent[];
  isRunning: boolean;
}

export function EvolutionViewer({ events, isRunning }: Props) {
  const genEvents = events.filter((e) => e.event_type === "generation");
  const progressEvents = events.filter((e) => e.event_type === "progress");

  // Find the highest generation that has a completed "generation" event
  const completedGens = new Set(genEvents.map((e) => e.generation));

  // Collect in-progress variants (progress events for gen not yet "complete")
  const liveByGen: Record<number, GenerationEvent[]> = {};
  for (const ev of progressEvents) {
    if (!completedGens.has(ev.generation)) {
      (liveByGen[ev.generation] ??= []).push(ev);
    }
  }

  const hasContent = genEvents.length > 0 || Object.keys(liveByGen).length > 0;
  if (!hasContent && !isRunning) return null;

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
              key={`gen-${ev.generation}`}
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

        {/* Live in-progress generation blocks */}
        {Object.entries(liveByGen).map(([genStr, evs]) => {
          const gen = Number(genStr);
          const bestSoFar = Math.max(...evs.map((e) => e.best_score));
          const topVariant = evs
            .flatMap((e) => e.variants)
            .sort((a, b) => b.score - a.score)[0];
          return (
            <div
              key={`live-${gen}`}
              className="border border-accent-teal/30 rounded bg-elevated p-3 opacity-70"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-muted">
                  Gen {gen}{" "}
                  <span className="text-accent-teal animate-pulse">·</span>
                </span>
                <span className="text-xs font-mono text-muted">
                  {evs.length} variant{evs.length !== 1 ? "s" : ""} so far
                  {" · "}best: {(bestSoFar * 100).toFixed(0)}%
                </span>
              </div>
              {topVariant && (
                <p className="text-xs text-muted font-mono italic leading-relaxed truncate">
                  {topVariant.reason}
                </p>
              )}
            </div>
          );
        })}

        {isRunning && !hasContent && (
          <div className="text-xs font-mono text-muted animate-pulse">
            Starting evolution…
          </div>
        )}
      </div>
    </div>
  );
}
