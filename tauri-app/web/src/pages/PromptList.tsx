import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { PromptSummary } from "../types";
import { getBaseUrl } from "../types";
import { C, S } from "../styles/theme";

export function PromptList() {
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);
  const navigate = useNavigate();

  async function load() {
    fetch(`${getBaseUrl()}/api/prompts`).then(r => r.json()).then(setPrompts).catch(() => {});
  }

  useEffect(() => { load(); }, []);

  async function deletePrompt(name: string) {
    await fetch(`${getBaseUrl()}/api/prompts/${name}`, { method: "DELETE" });
    load();
  }

  return (
    <div style={S.page}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <h1 style={S.pageTitle}>Prompts</h1>
        <button onClick={() => navigate("/prompts/new")} style={S.btnPrimary}>+ New Prompt</button>
      </div>

      {prompts.length === 0 ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, paddingTop: 64 }}>
          <p style={{ color: C.muted, fontFamily: "monospace", fontSize: 13 }}>No prompts yet — create one to get started.</p>
          <button onClick={() => navigate("/prompts/new")} style={S.btnPrimary}>New Prompt</button>
        </div>
      ) : (
        <div>
          {prompts.map(p => (
            <div key={p.name} style={S.card}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ color: C.text, fontFamily: "monospace", fontSize: 13, margin: 0 }}>{p.name}</p>
                <span style={{ color: C.muted, fontFamily: "monospace", fontSize: 11, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "block", marginTop: 2 }}>
                  {p.description_goal.slice(0, 72)}
                </span>
              </div>
              <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                <button onClick={() => navigate(`/prompts/${p.name}/run`)} style={S.btnRun}>Run</button>
                <button onClick={() => navigate(`/prompts/${p.name}/use`)} style={S.btnUse}>Use</button>
                <button onClick={() => navigate(`/prompts/${p.name}/edit`)} style={S.btnEdit}>Edit</button>
                <button onClick={() => deletePrompt(p.name)} style={S.btnDel}>Del</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
