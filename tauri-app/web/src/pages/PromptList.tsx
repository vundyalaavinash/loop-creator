import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { PromptSummary } from "../types";
import { getBaseUrl } from "../types";

export function PromptList() {
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);

  useEffect(() => {
    fetch(`${getBaseUrl()}/api/prompts`)
      .then(r => r.json())
      .then(setPrompts);
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>Prompts</h2>
        <Link to="/prompts/new" style={{ color: "#01C7B1", textDecoration: "none", fontWeight: 600 }}>
          + New Prompt
        </Link>
      </div>
      {prompts.length === 0 ? (
        <p style={{ color: "#8A8A8A" }}>No prompts yet — create one to get started.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ color: "#8A8A8A", fontSize: 12, textAlign: "left" }}>
              <th style={{ padding: "8px 12px" }}>Name</th>
              <th style={{ padding: "8px 12px" }}>Goal</th>
              <th style={{ padding: "8px 12px" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {prompts.map(p => (
              <tr key={p.name} style={{ borderTop: "1px solid #383838" }}>
                <td style={{ padding: "12px", color: "#F0F0F0" }}>{p.name}</td>
                <td style={{ padding: "12px", color: "#8A8A8A" }}>{p.description_goal.slice(0, 60)}</td>
                <td style={{ padding: "12px", display: "flex", gap: 8 }}>
                  <Link to={`/prompts/${p.name}/run`} style={{ color: "#01C7B1" }}>Run</Link>
                  <Link to={`/prompts/${p.name}/use`} style={{ color: "#9B6DFF" }}>Use</Link>
                  <Link to={`/prompts/${p.name}/edit`} style={{ color: "#8A8A8A" }}>Edit</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
