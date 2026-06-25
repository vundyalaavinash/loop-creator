import { useParams, useNavigate } from "react-router-dom";
import { usePrompt } from "../hooks/usePrompt";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";
import { getBaseUrl } from "../types";
import { C, S } from "../styles/theme";

export function PromptDashboard() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const { events, bestVariant, isRunning, error, run, stop } = usePrompt();

  return (
    <div style={S.page}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <button onClick={() => navigate("/prompts")} style={S.btnSecondary}>← Prompts</button>
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
          <button onClick={() => navigate(`/prompts/${name}/edit`)} style={S.btnSecondary}>Edit</button>
          <button onClick={() => navigate(`/prompts/${name}/use`)} style={S.btnUse}>Use →</button>
        </div>
      </div>

      {error && <div style={S.errorBanner}>{error}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <EvolutionViewer events={events} isRunning={isRunning} />
        <ResultsPanel
          bestVariant={bestVariant}
          outputUrl={`${getBaseUrl()}/api/prompts/${name}/output`}
        />
      </div>
    </div>
  );
}
