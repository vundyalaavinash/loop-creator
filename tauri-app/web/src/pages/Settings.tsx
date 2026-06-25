import { useEffect, useState } from "react";
import type { AppConfig } from "../types";
import { getBaseUrl } from "../types";
import { C, S } from "../styles/theme";

const CLI_OPTIONS = ["claude", "ollama", "devin"];

export function Settings() {
  const [config, setConfig] = useState<AppConfig>({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${getBaseUrl()}/api/config`)
      .then(r => {
        if (!r.ok) throw new Error("Failed to load config");
        return r.json();
      })
      .then(setConfig)
      .catch(err => setError(err.message));
  }, []);

  const save = async () => {
    await fetch(`${getBaseUrl()}/api/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ ...S.page, maxWidth: 480 }}>
      <h1 style={{ ...S.pageTitle, marginBottom: 24 }}>Settings</h1>

      {error && <div style={S.errorBanner}>{error}</div>}

      {/* Whisper backend */}
      <div style={S.section}>
        <label style={S.label}>Whisper Backend</label>
        <div style={{ display: "flex", gap: 8 }}>
          {["local", "openai"].map(o => (
            <button key={o} style={S.chip(config.whisper_backend === o)}
              onClick={() => setConfig(c => ({ ...c, whisper_backend: o }))}>
              {o}
            </button>
          ))}
        </div>
      </div>

      {/* Whisper model */}
      <div style={S.section}>
        <label htmlFor="whisper-model" style={S.label}>Whisper Model</label>
        <input id="whisper-model" value={config.whisper_model}
          onChange={e => setConfig(c => ({ ...c, whisper_model: e.target.value }))}
          style={S.input} placeholder="base" />
      </div>

      {/* OpenAI key — only when backend is openai */}
      {config.whisper_backend === "openai" && (
        <div style={S.section}>
          <label htmlFor="openai-key" style={S.label}>OpenAI API Key</label>
          <input id="openai-key" type="password" value={config.openai_api_key}
            onChange={e => setConfig(c => ({ ...c, openai_api_key: e.target.value }))}
            style={S.input} placeholder="sk-…" />
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <button onClick={save} style={S.btnPrimary}>Save Settings</button>
        {saved && <span style={{ color: C.teal, fontFamily: "monospace", fontSize: 13 }}>Saved!</span>}
      </div>
    </div>
  );
}
