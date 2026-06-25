import { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";
import { useLoop } from "../hooks/useLoop";
import { getBaseUrl, Variant } from "../types";
import { C, S } from "../styles/theme";

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
    <div style={S.page}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <button onClick={() => navigate("/loops")} style={S.btnSecondary}>← Loops</button>
        <div style={{ flex: 1 }}>
          <h1 style={S.pageTitle}>{id}</h1>
          <span style={S.subtitle}>{isRunning ? "running…" : bestVariant ? "complete" : "idle"}</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {isRunning ? (
            <button onClick={stop} style={S.btnStop}>Stop</button>
          ) : (
            <button onClick={() => id && run(id)} style={S.btnPrimary}>Run</button>
          )}
          <button onClick={() => navigate(`/edit/${id}`)} style={S.btnSecondary}>Edit</button>
        </div>
      </div>

      {error && <div style={S.errorBanner}>{error}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <EvolutionViewer events={events} isRunning={isRunning} />
        <ResultsPanel bestVariant={bestVariant} />
      </div>
    </div>
  );
}
