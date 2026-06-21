import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LoopSummary, getBaseUrl } from "../types";

export function LoopList() {
  const [loops, setLoops] = useState<LoopSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  async function load() {
    const r = await fetch(`${getBaseUrl()}/api/loops`);
    setLoops(await r.json());
    setLoading(false);
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  async function deleteLoop(id: string) {
    await fetch(`${getBaseUrl()}/api/loops/${id}`, { method: "DELETE" });
    load();
  }

  if (loading) {
    return <div className="p-8 text-muted font-mono text-sm">Loading...</div>;
  }

  if (loops.length === 0) {
    return (
      <div className="p-8 flex flex-col items-center justify-center gap-4 text-center">
        <p className="text-muted font-mono">No loops yet — create one to get started.</p>
        <button
          onClick={() => navigate("/new")}
          className="px-4 py-2 bg-accent-teal text-base rounded font-mono text-sm hover:opacity-90 transition-opacity"
        >
          New Loop
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-primary font-sans font-semibold text-lg">Loops</h1>
        <button
          onClick={() => navigate("/new")}
          className="px-3 py-1.5 bg-accent-teal text-base rounded font-mono text-xs hover:opacity-90"
        >
          + New Loop
        </button>
      </div>
      <div className="space-y-2">
        {loops.map((loop) => (
          <div
            key={loop.id}
            className="bg-surface border border-border-color rounded-lg p-4 flex items-center gap-4"
          >
            {loop.active && (
              <span className="w-2 h-2 rounded-full bg-accent-teal animate-pulse flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-primary font-mono text-sm truncate">{loop.name}</p>
              <span className="text-xs font-mono text-accent-purple">{loop.loop_type}</span>
            </div>
            {loop.best_score !== null && (
              <span className="text-xs font-mono text-accent-teal flex-shrink-0">
                {Math.round(loop.best_score * 100)}%
              </span>
            )}
            <div className="flex gap-2 flex-shrink-0">
              <button
                onClick={() => navigate(`/loops/${loop.id}/run`, { state: { startRun: true } })}
                className="text-xs font-mono px-2 py-1 border border-accent-teal text-accent-teal rounded hover:bg-accent-teal hover:text-base transition-colors"
              >
                Run
              </button>
              <button
                onClick={() => navigate(`/edit/${loop.id}`)}
                className="text-xs font-mono px-2 py-1 border border-border-color text-muted rounded hover:text-primary transition-colors"
              >
                Edit
              </button>
              <button
                onClick={() => deleteLoop(loop.id)}
                className="text-xs font-mono px-2 py-1 border border-red-800 text-red-400 rounded hover:bg-red-900 transition-colors"
              >
                Del
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
