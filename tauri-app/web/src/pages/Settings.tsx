import { useEffect, useState } from "react";
import type { AppConfig } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function Settings() {
  const [config, setConfig] = useState<AppConfig>({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(`http://localhost:${port()}/api/config`)
      .then(r => r.json())
      .then(setConfig);
  }, []);

  const save = async () => {
    await fetch(`http://localhost:${port()}/api/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const field = (label: string, id: string, value: string, onChange: (v: string) => void, options?: string[]) => (
    <div style={{ marginBottom: 20 }}>
      <label htmlFor={id} style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
        {label}
      </label>
      {options ? (
        <select id={id} value={value} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", maxWidth: 320, background: "#2E2E2E", border: "1px solid #383838",
            borderRadius: 6, color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }}>
          {options.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input id={id} value={value} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", maxWidth: 320, background: "#2E2E2E", border: "1px solid #383838",
            borderRadius: 6, color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }} />
      )}
    </div>
  );

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ color: "#F0F0F0", marginBottom: 24 }}>Settings</h2>
      {field("Whisper Backend", "whisper-backend", config.whisper_backend,
        v => setConfig(c => ({ ...c, whisper_backend: v })), ["local", "openai"])}
      {field("Whisper Model", "whisper-model", config.whisper_model,
        v => setConfig(c => ({ ...c, whisper_model: v })))}
      {config.whisper_backend === "openai" &&
        field("OpenAI API Key", "openai-key", config.openai_api_key,
          v => setConfig(c => ({ ...c, openai_api_key: v })))}
      <button onClick={save}
        style={{ background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6,
          padding: "10px 24px", fontWeight: 700, cursor: "pointer", fontSize: 15 }}>
        Save Settings
      </button>
      {saved && <span style={{ color: "#01C7B1", marginLeft: 16, fontSize: 14 }}>Saved!</span>}
    </div>
  );
}
