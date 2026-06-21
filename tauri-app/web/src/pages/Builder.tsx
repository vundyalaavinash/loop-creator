import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { LoopSpec, getBaseUrl } from "../types";

const LOOP_TYPES = ["coding", "debugging", "docs", "rfc", "design", "prompt", "custom"] as const;
const CLI_OPTIONS = ["claude", "ollama", "devin"] as const;

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

const SECTION_LABEL = "text-xs font-mono text-muted uppercase tracking-widest mb-1";
const INPUT_CLS = "w-full bg-elevated border border-border-color rounded px-3 py-2 text-primary font-mono text-sm focus:outline-none focus:border-accent-teal";

export function Builder() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const [spec, setSpec] = useState<LoopSpec>(defaultSpec());
  const [mcpServers, setMcpServers] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`${getBaseUrl()}/api/context/mcp`)
      .then((r) => r.json())
      .then(setMcpServers)
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
    <div className="p-6 max-w-2xl">
      <h1 className="text-primary font-sans font-semibold text-lg mb-6">
        {id ? "Edit Loop" : "New Loop"}
      </h1>

      {/* 1. Loop ID */}
      <div className="mb-5">
        <label className={SECTION_LABEL}>Loop ID</label>
        <input className={INPUT_CLS} value={spec.id}
          onChange={(e) => set("id", e.target.value)} />
      </div>

      {/* 2. Loop Type */}
      <div className="mb-5">
        <label className={SECTION_LABEL}>Loop Type</label>
        <div className="grid grid-cols-4 gap-2">
          {LOOP_TYPES.map((t) => (
            <button key={t} onClick={() => set("type", t as LoopSpec["type"])}
              className={`py-2 px-2 rounded border font-mono text-xs transition-colors ${
                spec.type === t
                  ? "border-accent-teal text-accent-teal bg-elevated"
                  : "border-border-color text-muted hover:text-primary"
              }`}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Task */}
      <div className="mb-5">
        <label className={SECTION_LABEL}>Task</label>
        <textarea rows={3} className={INPUT_CLS} value={spec.task}
          placeholder="Describe what you want to accomplish..."
          onChange={(e) => set("task", e.target.value)} />
      </div>

      {/* 4. Goal */}
      <div className="mb-5">
        <label className={SECTION_LABEL}>Goal</label>
        <textarea rows={3} className={INPUT_CLS} value={spec.goal}
          placeholder="What does a perfect output look like?"
          onChange={(e) => set("goal", e.target.value)} />
      </div>

      {/* 5. Context */}
      <div className="mb-5 bg-surface rounded-lg border border-border-color p-4">
        <p className={SECTION_LABEL}>Context</p>
        <label className="flex items-center gap-2 text-sm text-primary font-mono mb-2 cursor-pointer">
          <input type="checkbox" checked={spec.context.project}
            onChange={(e) => set("context", { ...spec.context, project: e.target.checked })} />
          Scrape project context
        </label>
        <label className="flex items-center gap-2 text-sm text-primary font-mono mb-2 cursor-pointer">
          <input type="checkbox" checked={spec.context.history}
            onChange={(e) => set("context", { ...spec.context, history: e.target.checked })} />
          Include iteration history
        </label>
        <label className="block text-xs text-muted font-mono mb-1 mt-2">Project root (leave blank for CWD)</label>
        <input className={INPUT_CLS} value={spec.context.project_root}
          placeholder="/path/to/project"
          onChange={(e) => set("context", { ...spec.context, project_root: e.target.value })} />
        {mcpServers.length > 0 && (
          <div className="mt-3">
            <p className="text-xs text-muted font-mono mb-1">MCP servers (auto-discovered)</p>
            {mcpServers.map((s) => (
              <span key={s} className="inline-block mr-2 mb-1 text-xs font-mono px-2 py-0.5 bg-elevated border border-accent-purple text-accent-purple rounded">
                {s}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 6. Generator / Judge */}
      <div className="mb-5 bg-surface rounded-lg border border-border-color p-4">
        <p className={SECTION_LABEL}>Generator</p>
        <div className="flex gap-2 mb-3">
          {CLI_OPTIONS.map((c) => (
            <button key={c} onClick={() => set("generator", { ...spec.generator, cli: c })}
              className={`flex-1 py-1.5 rounded border font-mono text-xs transition-colors ${
                spec.generator.cli === c
                  ? "border-accent-teal text-accent-teal bg-elevated"
                  : "border-border-color text-muted hover:text-primary"
              }`}>
              {c}
            </button>
          ))}
        </div>
        <input className={INPUT_CLS} value={spec.generator.model}
          placeholder="model name (e.g. sonnet, llama3.2)"
          onChange={(e) => set("generator", { ...spec.generator, model: e.target.value })} />
      </div>

      {/* 7. GEPA Params */}
      <div className="mb-5 bg-surface rounded-lg border border-border-color p-4">
        <p className={SECTION_LABEL}>GEPA Params</p>
        <div className="grid grid-cols-2 gap-3">
          {([
            ["Population size", "population_size"],
            ["Max generations", "max_generations"],
            ["Top-K survivors", "top_k"],
            ["Stagnation limit", "stagnation_limit"],
          ] as const).map(([label, key]) => (
            <div key={key}>
              <label className="text-xs text-muted font-mono">{label}</label>
              <input type="number" className={INPUT_CLS}
                value={spec.gepa[key]}
                onChange={(e) => set("gepa", { ...spec.gepa, [key]: parseInt(e.target.value) || 1 })} />
            </div>
          ))}
          <div className="col-span-2">
            <label className="text-xs text-muted font-mono">Fitness threshold (0-1)</label>
            <input type="number" step="0.05" min="0" max="1" className={INPUT_CLS}
              value={spec.gepa.fitness_threshold}
              onChange={(e) => set("gepa", { ...spec.gepa, fitness_threshold: parseFloat(e.target.value) || 0.85 })} />
          </div>
        </div>
      </div>

      {/* Preview + actions */}
      <div className="mb-5 bg-surface rounded-lg border border-border-color p-4">
        <p className={SECTION_LABEL}>Preview</p>
        <pre className="text-xs font-mono text-muted whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">
          {JSON.stringify(spec, null, 2)}
        </pre>
      </div>

      <div className="flex gap-3">
        <button onClick={() => save(false)} disabled={saving}
          className="px-4 py-2 bg-elevated border border-border-color text-primary font-mono text-sm rounded hover:border-accent-teal transition-colors disabled:opacity-50">
          Save
        </button>
        <button onClick={() => save(true)} disabled={saving}
          className="px-4 py-2 bg-accent-teal text-base font-mono text-sm rounded hover:opacity-90 transition-opacity disabled:opacity-50">
          Save & Run
        </button>
      </div>
    </div>
  );
}
