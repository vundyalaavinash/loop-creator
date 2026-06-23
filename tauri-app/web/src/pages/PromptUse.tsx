import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { PromptSpec } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function PromptUse() {
  const { name } = useParams<{ name: string }>();
  const [spec, setSpec] = useState<PromptSpec | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [resolved, setResolved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`http://localhost:${port()}/api/prompts/${name}`, { signal: controller.signal })
      .then(r => r.json())
      .then((s: PromptSpec) => {
        setSpec(s);
        setValues(Object.fromEntries(s.variables.map(v => [v, ""])));
      });
    return () => controller.abort();
  }, [name]);

  const fill = async () => {
    setError(null);
    try {
      const res = await fetch(`http://localhost:${port()}/api/prompts/${name}/use`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variables: values }),
      });
      const data = await res.json();
      setResolved(data.resolved);
    } catch (err: any) {
      setError(err?.message ?? "Failed to fill prompt");
    }
  };

  if (!spec) return <div style={{ padding: 24, color: "#8A8A8A" }}>Loading…</div>;

  return (
    <div style={{ padding: 24, maxWidth: 700 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <Link to="/prompts" style={{ color: "#8A8A8A", textDecoration: "none" }}>← Prompts</Link>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>Use: {name}</h2>
      </div>
      {spec.variables.map(v => (
        <div key={v} style={{ marginBottom: 16 }}>
          <label htmlFor={v} style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
            {v}
          </label>
          <textarea id={v} value={values[v] ?? ""} rows={3}
            onChange={e => setValues(prev => ({ ...prev, [v]: e.target.value }))}
            style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
              color: "#F0F0F0", padding: "8px 12px", fontSize: 14, resize: "vertical" }} />
        </div>
      ))}
      <button onClick={fill}
        style={{ background: "#9B6DFF", color: "#1C1C1C", border: "none", borderRadius: 6,
          padding: "10px 24px", fontWeight: 700, cursor: "pointer", fontSize: 15, marginBottom: 24 }}>
        Fill Prompt
      </button>
      {error && <p style={{ color: "#FF6B6B" }}>{error}</p>}
      {resolved && (
        <div style={{ background: "#2E2E2E", border: "1px solid #383838", borderRadius: 8, padding: 16 }}>
          <p style={{ color: "#8A8A8A", margin: "0 0 8px", fontSize: 12 }}>RESOLVED PROMPT</p>
          <pre style={{ color: "#F0F0F0", whiteSpace: "pre-wrap", margin: 0, fontSize: 14 }}>{resolved}</pre>
        </div>
      )}
    </div>
  );
}
