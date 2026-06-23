import { useParams, Link } from "react-router-dom";
import { useSkill } from "../hooks/useSkill";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";
import { getBaseUrl } from "../types";

export function SkillDashboard() {
  const { name } = useParams<{ name: string }>();
  const { events, bestVariant, isRunning, error, run, stop } = useSkill();

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <Link to="/skills" style={{ color: "#8A8A8A", textDecoration: "none" }}>← Skills</Link>
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
        <Link to={`/skills/${name}/edit`}
          style={{ color: "#9B6DFF", textDecoration: "none", marginLeft: "auto" }}>
          Edit
        </Link>
      </div>
      {error && <p style={{ color: "#ff6b6b" }}>{error}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <EvolutionViewer events={events} isRunning={isRunning} />
        <ResultsPanel
          bestVariant={bestVariant}
          outputUrl={`${getBaseUrl()}/api/skills/${name}/output`}
        />
      </div>
    </div>
  );
}
