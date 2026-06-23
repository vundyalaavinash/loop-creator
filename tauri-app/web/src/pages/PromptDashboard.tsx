import { useParams, Link } from "react-router-dom";
import { usePrompt } from "../hooks/usePrompt";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function PromptDashboard() {
  const { name } = useParams<{ name: string }>();
  const { events, bestVariant, isRunning, error, run, stop } = usePrompt();

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <Link to="/prompts" style={{ color: "#8A8A8A", textDecoration: "none" }}>← Prompts</Link>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>{name}</h2>
        {isRunning ? (
          <button onClick={stop}
            style={{ background: "#9B6DFF", color: "#1C1C1C", border: "none", borderRadius: 6,
              padding: "8px 20px", fontWeight: 700, cursor: "pointer" }}>
            Stop
          </button>
        ) : (
          <button onClick={() => run(name!)}
            style={{ background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6,
              padding: "8px 20px", fontWeight: 700, cursor: "pointer" }}>
            Run
          </button>
        )}
        <Link to={`/prompts/${name}/use`}
          style={{ color: "#9B6DFF", textDecoration: "none", marginLeft: "auto" }}>
          Use →
        </Link>
      </div>
      {error && <p style={{ color: "#ff6b6b" }}>{error}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <EvolutionViewer events={events} />
        <ResultsPanel
          bestVariant={bestVariant}
          outputUrl={`http://localhost:${port()}/api/prompts/${name}/output`}
        />
      </div>
    </div>
  );
}
