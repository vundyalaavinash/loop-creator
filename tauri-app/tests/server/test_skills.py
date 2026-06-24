import json, yaml, pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from creator.gepa.engine import GenerationEvent, Variant
from creator.skills.spec import SkillSpec
from creator.spec import GeneratorSpec, JudgeSpec


def _make_skill(tmp_path, name="myskill"):
    d = tmp_path / ".creator" / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    spec = SkillSpec(
        name=name, description_goal="Do code review", category="code-review",
        generator=GeneratorSpec(cli="claude"), judge=JudgeSpec(cli="claude"),
    )
    (d / "spec.yaml").write_text(yaml.dump(spec.model_dump()))
    return d


def _fake_variant():
    return Variant(prompt="p", output="# myskill\nDo reviews.", score=0.91, reason="great", generation=1)


def _fake_run_skill(spec, skill_dir, on_event=None):
    v = _fake_variant()
    ev = GenerationEvent(generation=1, variants=[v], best_score=0.91)
    done = GenerationEvent(generation=1, variants=[v], best_score=0.91, event_type="done")
    if on_event:
        on_event(ev)
        on_event(done)
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(v.output)
    return v


def test_list_skills(client, tmp_path):
    _make_skill(tmp_path, "alpha")
    _make_skill(tmp_path, "beta")
    r = client.get("/api/skills")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()]
    assert "alpha" in names and "beta" in names


def test_create_skill(client, tmp_path):
    payload = {
        "name": "newskill", "description_goal": "Do stuff", "category": "custom",
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    r = client.post("/api/skills", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "newskill"
    assert (tmp_path / ".creator" / "skills" / "newskill" / "spec.yaml").exists()


def test_get_skill(client, tmp_path):
    _make_skill(tmp_path, "getme")
    r = client.get("/api/skills/getme")
    assert r.status_code == 200
    assert r.json()["name"] == "getme"


def test_delete_skill(client, tmp_path):
    _make_skill(tmp_path, "deleteme")
    r = client.delete("/api/skills/deleteme")
    assert r.status_code == 200
    assert not (tmp_path / ".creator" / "skills" / "deleteme").exists()


def test_run_skill_streams_sse(client, tmp_path):
    _make_skill(tmp_path)
    with patch("lc_server.routes.skills.run_skill", _fake_run_skill):
        r = client.post("/api/skills/myskill/run")
    assert "text/event-stream" in r.headers["content-type"]
    assert "data: " in r.text
    assert "generation" in r.text


def test_get_skill_output(client, tmp_path):
    d = _make_skill(tmp_path)
    (d / "SKILL.md").write_text("# myskill\nDo reviews.")
    r = client.get("/api/skills/myskill/output")
    assert r.status_code == 200
    assert r.json()["content"].startswith("# myskill")


def test_publish_skill(client, tmp_path):
    d = _make_skill(tmp_path)
    (d / "SKILL.md").write_text("# myskill\n")
    claude_skills = tmp_path / ".claude" / "skills"
    with patch("creator.skills.registry._claude_skills_base", new=lambda: claude_skills):
        r = client.post("/api/skills/myskill/publish")
    assert r.status_code == 200
    assert "dest" in r.json()
    # Actually verify the file was published to the right place
    assert (claude_skills / "myskill" / "SKILL.md").exists()
