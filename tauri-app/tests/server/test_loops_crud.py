import json
import yaml
import pytest
from pathlib import Path


def _make_loop(tmp_path, loop_id="myloop"):
    d = tmp_path / ".loop-creator" / loop_id
    d.mkdir(parents=True, exist_ok=True)
    spec = {
        "id": loop_id, "type": "coding", "task": "write tests",
        "goal": "100% coverage",
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    (d / "spec.yaml").write_text(yaml.dump(spec))
    return d


def test_create_loop(client, tmp_path):
    payload = {
        "id": "newloop", "type": "coding", "task": "do stuff", "goal": "do it well",
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    r = client.post("/api/loops", json=payload)
    assert r.status_code == 200
    assert r.json()["id"] == "newloop"
    loop_dir = tmp_path / ".loop-creator" / "newloop"
    assert (loop_dir / "spec.yaml").exists()


def test_list_loops_returns_saved(client, tmp_path):
    _make_loop(tmp_path, "alpha")
    _make_loop(tmp_path, "beta")
    r = client.get("/api/loops")
    assert r.status_code == 200
    ids = [l["id"] for l in r.json()]
    assert "alpha" in ids
    assert "beta" in ids


def test_get_loop(client, tmp_path):
    _make_loop(tmp_path, "getme")
    r = client.get("/api/loops/getme")
    assert r.status_code == 200
    assert r.json()["id"] == "getme"


def test_delete_loop(client, tmp_path):
    _make_loop(tmp_path, "deleteme")
    r = client.delete("/api/loops/deleteme")
    assert r.status_code == 200
    assert not (tmp_path / ".loop-creator" / "deleteme").exists()
