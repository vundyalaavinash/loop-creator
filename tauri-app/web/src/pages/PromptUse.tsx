import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { PromptSpec } from "../types";
import { getBaseUrl } from "../types";
import { C, S } from "../styles/theme";

export function PromptUse() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [spec, setSpec] = useState<PromptSpec | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [resolved, setResolved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${getBaseUrl()}/api/prompts/${name}`, { signal: controller.signal })
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
      const res = await fetch(`${getBaseUrl()}/api/prompts/${name}/use`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variables: values }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error ?? "Request failed");
      setResolved(data.resolved);
    } catch (err: any) {
      setError(err?.message ?? "Failed to fill prompt");
    }
  };

  if (!spec) return <div style={{ ...S.page, color: C.muted, fontFamily: "monospace", fontSize: 13 }}>Loading…</div>;

  return (
    <div style={{ ...S.page, maxWidth: 680 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <button onClick={() => navigate("/prompts")} style={S.btnSecondary}>← Prompts</button>
        <h1 style={S.pageTitle}>Use: {name}</h1>
      </div>

      {spec.variables.map(v => (
        <div key={v} style={S.section}>
          <label htmlFor={v} style={S.label}>{v}</label>
          <textarea id={v} value={values[v] ?? ""} rows={3}
            onChange={e => setValues(prev => ({ ...prev, [v]: e.target.value }))}
            style={S.textarea} />
        </div>
      ))}

      <button onClick={fill} style={{ ...S.btnPrimary, marginBottom: 24 }}>Fill Prompt</button>

      {error && <div style={S.errorBanner}>{error}</div>}

      {resolved && (
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: 16 }}>
          <p style={{ color: C.muted, margin: "0 0 8px", fontSize: 12, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: 1 }}>Resolved Prompt</p>
          <pre style={{ color: C.text, whiteSpace: "pre-wrap", margin: 0, fontSize: 13, fontFamily: "monospace" }}>{resolved}</pre>
        </div>
      )}
    </div>
  );
}
