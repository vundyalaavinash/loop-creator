import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LoopSummary, getBaseUrl } from "../types";
import { C, S } from "../styles/theme";

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

  if (loading) return <div style={{ ...S.page, color: C.muted, fontFamily: "monospace", fontSize: 13 }}>Loading…</div>;

  return (
    <div style={S.page}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <h1 style={S.pageTitle}>Loops</h1>
        <button onClick={() => navigate("/new")} style={S.btnPrimary}>+ New Loop</button>
      </div>

      {loops.length === 0 ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, paddingTop: 64 }}>
          <p style={{ color: C.muted, fontFamily: "monospace", fontSize: 13 }}>No loops yet — create one to get started.</p>
          <button onClick={() => navigate("/new")} style={S.btnPrimary}>New Loop</button>
        </div>
      ) : (
        <div>
          {loops.map((loop) => (
            <div key={loop.id} style={S.card}>
              {loop.active && (
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: C.teal, flexShrink: 0, boxShadow: `0 0 6px ${C.teal}` }} />
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ color: C.text, fontFamily: "monospace", fontSize: 13, margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{loop.name}</p>
                <span style={S.tag(C.purple)}>{loop.loop_type}</span>
              </div>
              {loop.best_score !== null && (
                <span style={{ color: C.teal, fontFamily: "monospace", fontSize: 12, flexShrink: 0 }}>
                  {Math.round(loop.best_score * 100)}%
                </span>
              )}
              <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                <button onClick={() => navigate(`/loops/${loop.id}/run`, { state: { startRun: true } })} style={S.btnRun}>Run</button>
                <button onClick={() => navigate(`/edit/${loop.id}`)} style={S.btnEdit}>Edit</button>
                <button onClick={() => deleteLoop(loop.id)} style={S.btnDel}>Del</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
