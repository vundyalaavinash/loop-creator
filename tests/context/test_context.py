import json, os, tempfile
from loop_creator.context.project import scrape_project
from loop_creator.context.history import append_history, load_history_summary
from loop_creator.context.external import load_external
from loop_creator.context.bundle import build_bundle


def test_scrape_project_returns_string(tmp_path):
    (tmp_path / "README.md").write_text("# My Project")
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"')
    result = scrape_project(str(tmp_path))
    assert "README" in result or "pyproject" in result


def test_append_and_load_history(tmp_path):
    loop_dir = str(tmp_path)
    append_history(loop_dir, {"generation": 1, "score": 0.8, "prompt": "p1", "reason": "good"})
    append_history(loop_dir, {"generation": 2, "score": 0.5, "prompt": "p2", "reason": "ok"})
    summary = load_history_summary(loop_dir)
    assert "0.8" in summary or "p1" in summary


def test_load_external_reads_file(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Design Doc\nImportant details here.")
    result = load_external([str(f)])
    assert "Important details here" in result


def test_load_external_skips_missing_file():
    result = load_external(["/nonexistent/path.md"])
    assert "not found" in result.lower() or result == ""


def test_build_bundle_joins_sections():
    result = build_bundle(project="proj info", history="hist info", external="ext info")
    assert "proj info" in result
    assert "hist info" in result
    assert "ext info" in result


def test_build_bundle_respects_token_budget():
    big = "word " * 10000
    result = build_bundle(project=big, token_budget=500)
    assert len(result.split()) <= 600
