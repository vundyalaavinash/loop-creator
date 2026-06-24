import tempfile, os, yaml, pytest
from creator.spec import LoopSpec, GeneratorSpec, JudgeSpec, ContextSpec, GEPAParams, load_spec, save_spec


MINIMAL_YAML = """
id: test-loop
type: coding
task: Fix the bug
goal: All tests pass
generator:
  cli: claude
judge:
  cli: ollama
"""


def test_load_spec_from_yaml(tmp_path):
    p = tmp_path / "loop.yaml"
    p.write_text(MINIMAL_YAML)
    spec = load_spec(str(p))
    assert spec.id == "test-loop"
    assert spec.type == "coding"
    assert spec.generator.cli == "claude"
    assert spec.judge.cli == "ollama"


def test_defaults_applied():
    p_data = {"id": "x", "type": "custom", "task": "t", "goal": "g",
               "generator": {"cli": "claude"}, "judge": {"cli": "claude"}}
    spec = LoopSpec(**p_data)
    assert spec.gepa.population_size == 5
    assert spec.gepa.top_k == 2
    assert spec.context.project is True


def test_save_and_reload(tmp_path):
    spec = LoopSpec(id="s1", type="coding", task="t", goal="g",
                    generator=GeneratorSpec(cli="claude"),
                    judge=JudgeSpec(cli="ollama"))
    path = str(tmp_path / "out.yaml")
    save_spec(spec, path)
    loaded = load_spec(path)
    assert loaded.id == "s1"
    assert loaded.generator.cli == "claude"


def test_invalid_type_raises():
    with pytest.raises(Exception):
        LoopSpec(id="x", type="invalid_type", task="t", goal="g",
                 generator=GeneratorSpec(cli="claude"),
                 judge=JudgeSpec(cli="claude"))
