import yaml
import pytest
from unittest.mock import patch
from pathlib import Path
from creator.gepa.engine import GenerationEvent, Variant


def _fake_variant():
    return Variant(prompt="p", output="o", score=0.9, reason="great", generation=1)


def _fake_run_loop(spec, loop_dir, on_event=None):
    v = _fake_variant()
    ev = GenerationEvent(generation=1, variants=[v], best_score=0.9)
    done = GenerationEvent(generation=1, variants=[v], best_score=0.9, event_type="done")
    if on_event:
        on_event(ev)
        on_event(done)
    return v


def _make_loop(tmp_path, loop_id="runme"):
    d = tmp_path / ".creator" / "loops" / loop_id
    d.mkdir(parents=True, exist_ok=True)
    spec = {
        "id": loop_id, "type": "coding", "task": "t", "goal": "g",
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    (d / "spec.yaml").write_text(yaml.dump(spec))
    return d


def test_run_streams_event_data(client, tmp_path):
    d = _make_loop(tmp_path)
    with patch("lc_server.routes.loops.run_loop", _fake_run_loop):
        r = client.post("/api/loops/runme/run")
    assert "text/event-stream" in r.headers["content-type"]
    assert "data: " in r.text
    assert "generation" in r.text


def test_run_returns_404_for_missing_loop(client):
    r = client.post("/api/loops/ghost/run")
    assert r.status_code == 404


def test_history_returns_jsonl_as_array(client, tmp_path):
    d = _make_loop(tmp_path, "histloop")
    import json
    (d / "history.jsonl").write_text(
        json.dumps({"generation": 1, "score": 0.8, "prompt": "p", "reason": "r"}) + "\n"
    )
    r = client.get("/api/loops/histloop/history")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert data[0]["score"] == 0.8


def test_best_returns_markdown(client, tmp_path):
    d = _make_loop(tmp_path, "bestloop")
    (d / "best.md").write_text("# Best Result\n\nScore: 0.9\n")
    r = client.get("/api/loops/bestloop/best")
    assert r.status_code == 200
    assert r.json()["content"].startswith("# Best Result")
