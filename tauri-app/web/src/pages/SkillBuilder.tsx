import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { SkillTemplate, getBaseUrl } from "../types";
import { pickFolder, pickFiles } from "../utils/dialog";

const CATEGORIES = ["code-review", "testing", "documentation", "devops", "data-analysis", "custom"];
const CLI_OPTIONS = ["claude", "ollama", "devin"];

const S = {
  label: { display: "block" as const, color: "#6B7280", marginBottom: 4, fontSize: 12, fontFamily: "monospace", textTransform: "uppercase" as const, letterSpacing: 1 },
  input: { width: "100%", background: "#111111", border: "1px solid #1E1E1E", borderRadius: 6, color: "#FFFFFF", padding: "8px 12px", fontSize: 14, fontFamily: "monospace", boxSizing: "border-box" as const },
  textarea: { width: "100%", background: "#111111", border: "1px solid #1E1E1E", borderRadius: 6, color: "#FFFFFF", padding: "8px 12px", fontSize: 14, fontFamily: "monospace", resize: "vertical" as const, boxSizing: "border-box" as const },
  section: { background: "#0A0A0A", border: "1px solid #1E1E1E", borderRadius: 8, padding: 16, marginBottom: 16 },
  chip: (active: boolean) => ({
    padding: "6px 14px", borderRadius: 6, border: `1px solid ${active ? "#01C7B1" : "#1E1E1E"}`,
    color: active ? "#01C7B1" : "#6B7280", background: active ? "#111111" : "transparent",
    cursor: "pointer" as const, fontSize: 12, fontFamily: "monospace",
  }),
  btnPrimary: { background: "#01C7B1", color: "#000000", border: "none", borderRadius: 6, padding: "10px 24px", fontWeight: 700, cursor: "pointer" as const, fontSize: 14, fontFamily: "monospace" },
  btnSecondary: { background: "#111111", color: "#FFFFFF", border: "1px solid #1E1E1E", borderRadius: 6, padding: "10px 24px", fontWeight: 600, cursor: "pointer" as const, fontSize: 14, fontFamily: "monospace" },
  btnBrowse: { background: "transparent", color: "#01C7B1", border: "1px solid #1E1E1E", borderRadius: 6, padding: "6px 14px", cursor: "pointer" as const, fontSize: 12, fontFamily: "monospace", whiteSpace: "nowrap" as const },
};

export function SkillBuilder() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "", description_goal: "", category: "custom",
    generator_cli: "claude", generator_model: "",
    judge_cli: "claude",
    project_root: "", include_files: [] as string[],
  });
  const [error, setError] = useState<string | null>(null);
  const [templates, setTemplates] = useState<SkillTemplate[]>([]);

  useEffect(() => {
    fetch(`${getBaseUrl()}/api/templates/skills`)
      .then(r => r.json())
      .then(setTemplates)
      .catch(() => {});

    if (name) {
      fetch(`${getBaseUrl()}/api/skills/${name}`)
        .then(r => r.json())
        .then(spec => setForm(f => ({
          ...f,
          name: spec.name, description_goal: spec.description_goal, category: spec.category,
          generator_cli: spec.generator?.cli ?? "claude",
          generator_model: spec.generator?.model ?? "",
          judge_cli: spec.judge?.cli ?? "claude",
          project_root: spec.context?.project_root ?? "",
          include_files: spec.context?.include_files ?? [],
        })));
    }
  }, [name]);

  function applyTemplate(t: SkillTemplate) {
    setForm(f => ({
      ...f,
      description_goal: t.description_goal,
      category: t.category,
      generator_cli: t.generator_cli,
      judge_cli: t.judge_cli,
    }));
  }

  function removeFile(path: string) {
    setForm(f => ({ ...f, include_files: f.include_files.filter(p => p !== path) }));
  }

  const save = async () => {
    setError(null);
    const payload = {
      name: form.name,
      description_goal: form.description_goal,
      category: form.category,
      generator: { cli: form.generator_cli, model: form.generator_model },
      judge: { cli: form.judge_cli, rubric: "", model: "" },
      context: {
        project_root: form.project_root,
        include_files: form.include_files,
      },
    };
    const res = await fetch(`${getBaseUrl()}/api/skills`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError((data as any)?.detail ?? "Save failed");
      return;
    }
    navigate("/skills");
  };

  return (
    <div style={{ padding: 24, maxWidth: 640 }}>
      <h2 style={{ color: "#FFFFFF", fontFamily: "sans-serif", fontWeight: 600, fontSize: 18, marginBottom: 24 }}>
        {name ? "Edit Skill" : "New Skill"}
      </h2>

      {/* Template picker */}
      {templates.length > 0 && (
        <div style={{ ...S.section, marginBottom: 24 }}>
          <span style={S.label}>Start from a template</span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
            {templates.map(t => (
              <button key={t.id} style={S.chip(false)} onClick={() => applyTemplate(t)} title={t.description}>
                {t.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Skill Name */}
      <div style={S.section}>
        <label htmlFor="skill-name" style={S.label}>Skill Name</label>
        <input id="skill-name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          style={S.input} />
      </div>

      {/* Description Goal */}
      <div style={S.section}>
        <label htmlFor="description-goal" style={S.label}>Description Goal</label>
        <textarea id="description-goal" value={form.description_goal}
          onChange={e => setForm(f => ({ ...f, description_goal: e.target.value }))}
          rows={4} style={S.textarea} />
      </div>

      {/* Category */}
      <div style={S.section}>
        <label style={S.label}>Category</label>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {CATEGORIES.map(c => (
            <button key={c} style={S.chip(form.category === c)}
              onClick={() => setForm(f => ({ ...f, category: c }))}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Generator CLI */}
      <div style={S.section}>
        <label style={S.label}>Generator CLI</label>
        <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
          {CLI_OPTIONS.map(c => (
            <button key={c} style={S.chip(form.generator_cli === c)}
              onClick={() => setForm(f => ({ ...f, generator_cli: c }))}>
              {c}
            </button>
          ))}
        </div>
        <input style={S.input} value={form.generator_model}
          placeholder="model name (optional)"
          onChange={e => setForm(f => ({ ...f, generator_model: e.target.value }))} />
      </div>

      {/* Judge CLI */}
      <div style={S.section}>
        <label style={S.label}>Judge CLI</label>
        <div style={{ display: "flex", gap: 8 }}>
          {CLI_OPTIONS.map(c => (
            <button key={c} style={S.chip(form.judge_cli === c)}
              onClick={() => setForm(f => ({ ...f, judge_cli: c }))}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* File Context */}
      <div style={S.section}>
        <label style={S.label}>File Context</label>

        <label style={{ ...S.label, marginBottom: 4 }}>Project Root</label>
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <input style={S.input} value={form.project_root}
            placeholder="/path/to/project (leave blank for CWD)"
            onChange={e => setForm(f => ({ ...f, project_root: e.target.value }))} />
          <button style={S.btnBrowse} onClick={async () => {
            const folder = await pickFolder();
            if (folder) setForm(f => ({ ...f, project_root: folder }));
          }}>Browse</button>
        </div>

        <label style={S.label}>Include Files</label>
        <button style={{ ...S.btnBrowse, marginBottom: 8 }} onClick={async () => {
          const files = await pickFiles();
          if (files.length) setForm(f => ({
            ...f,
            include_files: [...new Set([...f.include_files, ...files])],
          }));
        }}>+ Add Files</button>
        {form.include_files.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {form.include_files.map(p => (
              <div key={p} style={{ display: "flex", alignItems: "center", gap: 8, background: "#111111", border: "1px solid #1E1E1E", borderRadius: 4, padding: "4px 10px" }}>
                <span style={{ flex: 1, fontSize: 12, fontFamily: "monospace", color: "#FFFFFF", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p}</span>
                <button onClick={() => removeFile(p)} style={{ background: "none", border: "none", color: "#6B7280", cursor: "pointer", fontSize: 14, lineHeight: 1 }}>×</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <button onClick={save} style={S.btnPrimary}>Save Skill</button>
      {error && <p style={{ color: "#FF6B6B", marginTop: 12 }}>{error}</p>}
    </div>
  );
}
