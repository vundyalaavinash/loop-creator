import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { SkillSummary } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function SkillList() {
  const [skills, setSkills] = useState<SkillSummary[]>([]);

  useEffect(() => {
    fetch(`http://localhost:${port()}/api/skills`)
      .then(r => r.json())
      .then(setSkills);
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>Skills</h2>
        <Link to="/skills/new" style={{ color: "#01C7B1", textDecoration: "none", fontWeight: 600 }}>
          + New Skill
        </Link>
      </div>
      {skills.length === 0 ? (
        <p style={{ color: "#8A8A8A" }}>No skills yet — create one to get started.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ color: "#8A8A8A", fontSize: 12, textAlign: "left" }}>
              <th style={{ padding: "8px 12px" }}>Name</th>
              <th style={{ padding: "8px 12px" }}>Category</th>
              <th style={{ padding: "8px 12px" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {skills.map(s => (
              <tr key={s.name} style={{ borderTop: "1px solid #383838" }}>
                <td style={{ padding: "12px", color: "#F0F0F0" }}>{s.name}</td>
                <td style={{ padding: "12px", color: "#8A8A8A" }}>{s.category}</td>
                <td style={{ padding: "12px", display: "flex", gap: 8 }}>
                  <Link to={`/skills/${s.name}/run`} style={{ color: "#01C7B1" }}>Run</Link>
                  <Link to={`/skills/${s.name}/edit`} style={{ color: "#9B6DFF" }}>Edit</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
