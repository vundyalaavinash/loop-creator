import json, yaml, pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from creator.gepa.engine import GenerationEvent, Variant
from creator.prompts.spec import PromptSpec
from creator.spec import GeneratorSpec, JudgeSpec


def _make_prompt(tmp_path, name="myprompt"):
    d = tmp_path / ".creator" / "prompts" / name
    d.mkdir(parents=True, exist_ok=True)
    spec = PromptSpec(
        name=name, description_goal="Generate commit messages", variables=["diff"],
        generator=GeneratorSpec(cli="claude"), judge=JudgeSpec(cli="claude"),
    )
    (d / "spec.yaml").write_text(yaml.dump(spec.model_dump()))
    return d


def _fake_run_prompt(spec, prompt_dir, on_event=None):
    v = Variant(prompt="p", output="Write for {{diff}}.", score=0.92, reason="good", generation=1)
    ev = GenerationEvent(generation=1, variants=[v], best_score=0.92)
    done = GenerationEvent(generation=1, variants=[v], best_score=0.92, event_type="done")
    if on_event:
        on_event(ev); on_event(done)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / f"{spec.name}.md").write_text(v.output)
    return v


def test_list_prompts(client, tmp_path):
    _make_prompt(tmp_path, "a")
    _make_prompt(tmp_path, "b")
    r = client.get("/api/prompts")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert "a" in names and "b" in names


def test_create_prompt(client, tmp_path):
    payload = {
        "name": "newprompt", "description_goal": "Make commits", "variables": ["diff"],
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    r = client.post("/api/prompts", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "newprompt"


def test_delete_prompt(client, tmp_path):
    _make_prompt(tmp_path, "del")
    r = client.delete("/api/prompts/del")
    assert r.status_code == 200
    assert not (tmp_path / ".creator" / "prompts" / "del").exists()


def test_run_prompt_streams_sse(client, tmp_path):
    _make_prompt(tmp_path)
    with patch("lc_server.routes.prompts.run_prompt", _fake_run_prompt):
        r = client.post("/api/prompts/myprompt/run")
    assert "text/event-stream" in r.headers["content-type"]


def test_use_prompt(client, tmp_path):
    d = _make_prompt(tmp_path)
    (d / "myprompt.md").write_text("Write for {{diff}}.")
    r = client.post("/api/prompts/myprompt/use", json={"variables": {"diff": "added login"}})
    assert r.status_code == 200
    assert r.json()["resolved"] == "Write for added login."
