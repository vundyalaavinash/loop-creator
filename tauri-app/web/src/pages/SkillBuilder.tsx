import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const port = () => (window as any).__LC_PORT__ ?? 5001;
const CATEGORIES = ["code-review", "testing", "documentation", "devops", "data-analysis", "custom"];
const CLI_OPTIONS = ["claude", "ollama", "devin"];

export function SkillBuilder() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "", description_goal: "", category: "custom",
    generator_cli: "claude", judge_cli: "claude",
  });

  useEffect(() => {
    if (name) {
      fetch(`http://localhost:${port()}/api/skills/${name}`)
        .then(r => r.json())
        .then(spec => setForm({
          name: spec.name, description_goal: spec.description_goal, category: spec.category,
          generator_cli: spec.generator.cli, judge_cli: spec.judge.cli,
        }));
    }
  }, [name]);

  const save = async () => {
    const payload = {
      name: form.name, description_goal: form.description_goal, category: form.category,
      generator: { cli: form.generator_cli, model: "" },
      judge: { cli: form.judge_cli, rubric: "", model: "" },
    };
    await fetch(`http://localhost:${port()}/api/skills`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    navigate("/skills");
  };

  const field = (label: string, id: string, value: string, onChange: (v: string) => void, multiline = false) => (
    <div style={{ marginBottom: 16 }}>
      <label htmlFor={id} style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
        {label}
      </label>
      {multiline ? (
        <textarea id={id} value={value} onChange={e => onChange(e.target.value)}
          rows={4}
          style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
            color: "#F0F0F0", padding: "8px 12px", fontSize: 14, resize: "vertical" }} />
      ) : (
        <input id={id} value={value} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
            color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }} />
      )}
    </div>
  );

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <h2 style={{ color: "#F0F0F0", marginBottom: 24 }}>{name ? "Edit Skill" : "New Skill"}</h2>
      {field("Skill Name", "skill-name", form.name, v => setForm(f => ({ ...f, name: v })))}
      {field("Description Goal", "description-goal", form.description_goal,
        v => setForm(f => ({ ...f, description_goal: v })), true)}
      <div style={{ marginBottom: 16 }}>
        <label htmlFor="category" style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
          Category
        </label>
        <select id="category" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
          style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
            color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }}>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <button onClick={save}
        style={{ background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6,
          padding: "10px 24px", fontWeight: 700, cursor: "pointer", fontSize: 15 }}>
        Save Skill
      </button>
    </div>
  );
}
