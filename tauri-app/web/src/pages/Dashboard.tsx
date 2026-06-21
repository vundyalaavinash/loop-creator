import { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";
import { useLoop } from "../hooks/useLoop";
import { getBaseUrl, Variant } from "../types";

export function Dashboard() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { events, bestVariant: liveBest, isRunning, error, run, stop } = useLoop();
  const [staticBest, setStaticBest] = useState<Variant | null>(null);

  const bestVariant = liveBest ?? staticBest;

  useEffect(() => {
    if (!id) return;
    const startRun = (location.state as any)?.startRun ?? false;
    if (startRun) {
      run(id);
      return () => stop();
    }
    // Load best result statically for already-finished loops
    fetch(`${getBaseUrl()}/api/loops/${id}/best`)
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (!data?.content) return;
        const scoreMatch = data.content.match(/Score:\s*([\d.]+)/);
        const reasonMatch = data.content.match(/Reason:\s*([^\n]+)/);
        const outputMatch = data.content.match(/## Output\n\n([\s\S]+?)\n\n## Prompt/);
        const promptMatch = data.content.match(/## Prompt\n\n([\s\S]+)$/);
        setStaticBest({
          score: scoreMatch ? parseFloat(scoreMatch[1]) : 0,
          reason: reasonMatch ? reasonMatch[1].trim() : "",
          output: outputMatch ? outputMatch[1].trim() : "",
          prompt: promptMatch ? promptMatch[1].trim() : "",
          generation: 0,
        });
      })
      .catch(() => {});
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
