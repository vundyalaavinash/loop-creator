import { useParams, useNavigate } from "react-router-dom";
import { useSkill } from "../hooks/useSkill";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";
import { getBaseUrl } from "../types";
import { C, S } from "../styles/theme";

export function SkillDashboard() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const { events, bestVariant, isRunning, error, run, stop } = useSkill();

  return (
    <div style={S.page}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <button onClick={() => navigate("/skills")} style={S.btnSecondary}>← Skills</button>
        <div style={{ flex: 1 }}>
          <h1 style={S.pageTitle}>{name}</h1>
          <span style={S.subtitle}>{isRunning ? "running…" : bestVariant ? "complete" : "idle"}</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {isRunning ? (
            <button onClick={stop} style={S.btnStop}>Stop</button>
          ) : (
            <button onClick={() => name && run(name)} style={S.btnPrimary}>Run</button>
          )}
          <button onClick={() => navigate(`/skills/${name}/edit`)} style={S.btnSecondary}>Edit</button>
        </div>
      </div>

      {error && <div style={S.errorBanner}>{error}</div>}

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
