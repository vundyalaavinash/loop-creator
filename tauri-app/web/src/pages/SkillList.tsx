import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { SkillSummary } from "../types";
import { getBaseUrl } from "../types";
import { C, S } from "../styles/theme";

export function SkillList() {
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const navigate = useNavigate();

  async function load() {
    fetch(`${getBaseUrl()}/api/skills`).then(r => r.json()).then(setSkills).catch(() => {});
  }

  useEffect(() => { load(); }, []);

  async function deleteSkill(name: string) {
    await fetch(`${getBaseUrl()}/api/skills/${name}`, { method: "DELETE" });
    load();
  }

  return (
    <div style={S.page}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <h1 style={S.pageTitle}>Skills</h1>
        <button onClick={() => navigate("/skills/new")} style={S.btnPrimary}>+ New Skill</button>
      </div>

      {skills.length === 0 ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, paddingTop: 64 }}>
          <p style={{ color: C.muted, fontFamily: "monospace", fontSize: 13 }}>No skills yet — create one to get started.</p>
          <button onClick={() => navigate("/skills/new")} style={S.btnPrimary}>New Skill</button>
        </div>
      ) : (
        <div>
          {skills.map(s => (
            <div key={s.name} style={S.card}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ color: C.text, fontFamily: "monospace", fontSize: 13, margin: 0 }}>{s.name}</p>
                <span style={S.tag(C.purple)}>{s.category}</span>
              </div>
              <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                <button onClick={() => navigate(`/skills/${s.name}/run`)} style={S.btnRun}>Run</button>
                <button onClick={() => navigate(`/skills/${s.name}/edit`)} style={S.btnEdit}>Edit</button>
                <button onClick={() => deleteSkill(s.name)} style={S.btnDel}>Del</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
