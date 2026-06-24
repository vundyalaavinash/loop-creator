import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { LoopSpec, LoopTemplate, getBaseUrl } from "../types";

const LOOP_TYPES = ["coding", "debugging", "docs", "rfc", "design", "prompt", "custom"] as const;
const CLI_OPTIONS = ["claude", "ollama", "devin"] as const;

const S = {
  label: { display: "block" as const, color: "#8A8A8A", marginBottom: 4, fontSize: 12, fontFamily: "monospace", textTransform: "uppercase" as const, letterSpacing: 1 },
  input: { width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6, color: "#F0F0F0", padding: "8px 12px", fontSize: 14, fontFamily: "monospace", boxSizing: "border-box" as const },
  textarea: { width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6, color: "#F0F0F0", padding: "8px 12px", fontSize: 14, fontFamily: "monospace", resize: "vertical" as const, boxSizing: "border-box" as const },
  section: { background: "#242424", border: "1px solid #383838", borderRadius: 8, padding: 16, marginBottom: 16 },
  chip: (active: boolean) => ({
    padding: "6px 14px", borderRadius: 6, border: `1px solid ${active ? "#01C7B1" : "#383838"}`,
    color: active ? "#01C7B1" : "#8A8A8A", background: active ? "#2E2E2E" : "transparent",
    cursor: "pointer" as const, fontSize: 12, fontFamily: "monospace",
  }),
  btnPrimary: { background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6, padding: "10px 24px", fontWeight: 700, cursor: "pointer" as const, fontSize: 14, fontFamily: "monospace" },
  btnSecondary: { background: "#2E2E2E", color: "#F0F0F0", border: "1px solid #383838", borderRadius: 6, padding: "10px 24px", fontWeight: 600, cursor: "pointer" as const, fontSize: 14, fontFamily: "monospace" },
};

function defaultSpec(): LoopSpec {
  return {
    id: `loop-${Date.now()}`,
    type: "coding",
    task: "",
    goal: "",
    generator: { cli: "claude", model: "" },
    judge: { cli: "claude", rubric: "", model: "" },
    context: { project: true, history: true, external: [], mcp_auto_discover: true, project_root: "" },
    gepa: { population_size: 5, top_k: 2, max_generations: 10, fitness_threshold: 0.85, stagnation_limit: 3 },
  };
}

export function Builder() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const [spec, setSpec] = useState<LoopSpec>(defaultSpec());
  const [mcpServers, setMcpServers] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [templates, setTemplates] = useState<LoopTemplate[]>([]);

  useEffect(() => {
    fetch(`${getBaseUrl()}/api/context/mcp`)
      .then((r) => r.json())
      .then(setMcpServers)
      .catch(() => {});

    fetch(`${getBaseUrl()}/api/templates/loops`)
      .then((r) => r.json())
      .then(setTemplates)
      .catch(() => {});

    if (id) {
      fetch(`${getBaseUrl()}/api/loops/${id}`)
        .then((r) => r.json())
        .then(setSpec)
        .catch(() => {});
    }
  }, [id]);

  function set<K extends keyof LoopSpec>(key: K, val: LoopSpec[K]) {
    setSpec((s) => ({ ...s, [key]: val }));
  }

  function applyTemplate(t: LoopTemplate) {
    setSpec((s) => ({
      ...s,
      type: t.loop_type as LoopSpec["type"],
      task: t.task,
      goal: t.goal,
      generator: { ...s.generator, cli: t.generator_cli },
      judge: { ...s.judge, cli: t.judge_cli },
    }));
  }

  async function save(andRun = false) {
    setSaving(true);
    const r = await fetch(`${getBaseUrl()}/api/loops`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(spec),
    });
    setSaving(false);
    if (r.ok) {
      if (andRun) navigate(`/loops/${spec.id}/run`);
      else navigate("/loops");
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 640 }}>
      <h1 style={{ color: "#F0F0F0", fontFamily: "sans-serif", fontWeight: 600, fontSize: 18, marginBottom: 24 }}>
        {id ? "Edit Loop" : "New Loop"}
      </h1>

      {/* Template picker */}
      {templates.length > 0 && (
        <div style={{ ...S.section, marginBottom: 24 }}>
          <span style={S.label}>Start from a template</span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
            {templates.map(t => (
              <button key={t.id} style={S.chip(false)} onClick={() => applyTemplate(t)}
                title={t.description}>
                {t.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 1. Loop ID */}
      <div style={S.section}>
        <label style={S.label}>Loop ID</label>
        <input style={S.input} value={spec.id}
          onChange={(e) => set("id", e.target.value)} />
      </div>

      {/* 2. Loop Type */}
      <div style={S.section}>
        <label style={S.label}>Loop Type</label>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
          {LOOP_TYPES.map((t) => (
            <button key={t} style={S.chip(spec.type === t)}
              onClick={() => set("type", t as LoopSpec["type"])}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Task */}
      <div style={S.section}>
        <label style={S.label}>Task</label>
        <textarea rows={3} style={S.textarea} value={spec.task}
          placeholder="Describe what you want to accomplish..."
          onChange={(e) => set("task", e.target.value)} />
      </div>

      {/* 4. Goal */}
      <div style={S.section}>
        <label style={S.label}>Goal</label>
        <textarea rows={3} style={S.textarea} value={spec.goal}
          placeholder="What does a perfect output look like?"
          onChange={(e) => set("goal", e.target.value)} />
      </div>

      {/* 5. Context */}
      <div style={S.section}>
        <label style={S.label}>Context</label>
        <label style={{ display: "flex", alignItems: "center", gap: 8, color: "#F0F0F0", fontFamily: "monospace", fontSize: 13, marginBottom: 8, cursor: "pointer" }}>
          <input type="checkbox" checked={spec.context.project}
            onChange={(e) => set("context", { ...spec.context, project: e.target.checked })} />
          Scrape project context
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8, color: "#F0F0F0", fontFamily: "monospace", fontSize: 13, marginBottom: 8, cursor: "pointer" }}>
          <input type="checkbox" checked={spec.context.history}
            onChange={(e) => set("context", { ...spec.context, history: e.target.checked })} />
          Include iteration history
        </label>
        <label style={{ ...S.label, marginTop: 8 }}>Project root (leave blank for CWD)</label>
        <input style={S.input} value={spec.context.project_root}
          placeholder="/path/to/project"
          onChange={(e) => set("context", { ...spec.context, project_root: e.target.value })} />
        {mcpServers.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <span style={S.label}>MCP servers (auto-discovered)</span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
              {mcpServers.map((s) => (
                <span key={s} style={{ fontSize: 11, fontFamily: "monospace", padding: "2px 8px", background: "#2E2E2E", border: "1px solid #7C3AED", color: "#A78BFA", borderRadius: 4 }}>
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 6. Generator */}
      <div style={S.section}>
        <label style={S.label}>Generator</label>
        <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
          {CLI_OPTIONS.map((c) => (
            <button key={c} style={S.chip(spec.generator.cli === c)}
              onClick={() => set("generator", { ...spec.generator, cli: c })}>
              {c}
            </button>
          ))}
        </div>
        <input style={S.input} value={spec.generator.model}
          placeholder="model name (e.g. sonnet, llama3.2)"
          onChange={(e) => set("generator", { ...spec.generator, model: e.target.value })} />
      </div>

      {/* 7. Judge */}
      <div style={S.section}>
        <label style={S.label}>Judge</label>
        <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
          {CLI_OPTIONS.map((c) => (
            <button key={c} style={S.chip(spec.judge.cli === c)}
              onClick={() => set("judge", { ...spec.judge, cli: c })}>
              {c}
            </button>
          ))}
        </div>
        <input style={S.input} value={spec.judge.model}
          placeholder="model name (e.g. sonnet, llama3.2)"
          onChange={(e) => set("judge", { ...spec.judge, model: e.target.value })} />
      </div>

      {/* 8. GEPA Params */}
      <div style={S.section}>
        <label style={S.label}>GEPA Params</label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {([
            ["Population size", "population_size"],
            ["Max generations", "max_generations"],
            ["Top-K survivors", "top_k"],
            ["Stagnation limit", "stagnation_limit"],
          ] as const).map(([lbl, key]) => (
            <div key={key}>
              <label style={S.label}>{lbl}</label>
              <input type="number" style={S.input}
                value={spec.gepa[key]}
                onChange={(e) => set("gepa", { ...spec.gepa, [key]: parseInt(e.target.value) || 1 })} />
            </div>
          ))}
          <div style={{ gridColumn: "span 2" }}>
            <label style={S.label}>Fitness threshold (0-1)</label>
            <input type="number" step="0.05" min="0" max="1" style={S.input}
              value={spec.gepa.fitness_threshold}
              onChange={(e) => set("gepa", { ...spec.gepa, fitness_threshold: parseFloat(e.target.value) || 0.85 })} />
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        <button onClick={() => save(false)} disabled={saving} style={S.btnSecondary}>
          Save
        </button>
        <button onClick={() => save(true)} disabled={saving} style={S.btnPrimary}>
          Save & Run
        </button>
      </div>
    </div>
  );
}
