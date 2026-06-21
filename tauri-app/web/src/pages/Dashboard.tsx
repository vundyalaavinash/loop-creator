import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";
import { useLoop } from "../hooks/useLoop";

export function Dashboard() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { events, bestVariant, isRunning, error, run, stop } = useLoop();

  useEffect(() => {
    if (id) run(id);
    return () => stop();
  }, [id]);

  return (
    <div className="p-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-primary font-mono font-semibold">{id}</h1>
          <span className="text-xs text-muted font-mono">
            {isRunning ? "running…" : bestVariant ? "complete" : "idle"}
          </span>
        </div>
        <div className="flex gap-2">
          {isRunning && (
            <button onClick={stop}
              className="px-3 py-1.5 border border-red-700 text-red-400 font-mono text-xs rounded hover:bg-red-900 transition-colors">
              Stop
            </button>
          )}
          <button onClick={() => navigate("/loops")}
            className="px-3 py-1.5 border border-border-color text-muted font-mono text-xs rounded hover:text-primary transition-colors">
            ← Back
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900 border border-red-700 text-red-300 rounded font-mono text-xs">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <EvolutionViewer events={events} isRunning={isRunning} />
        <ResultsPanel bestVariant={bestVariant} />
      </div>
    </div>
  );
}
