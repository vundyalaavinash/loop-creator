import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from creator.gepa.engine import GEPAEngine, SEED_SYSTEM
from creator.spec import GEPAParams
from creator.adapters.base import LLMAdapter


class FakeAdapter(LLMAdapter):
    def __init__(self, output="result"):
        self._output = output
    def call(self, system, user): return self._output
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


class FakeJudge:
    def score(self, output, rubric): return (0.9, "good")


def test_engine_accepts_system_prompt():
    params = GEPAParams(population_size=2, max_generations=1, fitness_threshold=0.99)
    engine = GEPAEngine(
        generator=FakeAdapter(),
        judge=FakeJudge(),
        params=params,
        system_prompt="Custom system prompt",
    )
    assert engine.system_prompt == "Custom system prompt"


def test_engine_default_system_prompt():
    params = GEPAParams(population_size=2, max_generations=1, fitness_threshold=0.99)
    engine = GEPAEngine(generator=FakeAdapter(), judge=FakeJudge(), params=params)
    assert engine.system_prompt == SEED_SYSTEM


def test_run_skill_writes_skill_md(tmp_path):
    from creator.skills.spec import SkillSpec
    from creator.skills.runner import run_skill
    from creator.spec import GeneratorSpec, JudgeSpec

    spec = SkillSpec(
        name="testskill",
        description_goal="Write great code reviews",
        category="code-review",
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )

    fake_variant = MagicMock()
    fake_variant.output = "# testskill\n\nDo great code reviews."

    with patch("creator.skills.runner.build_adapter", return_value=FakeAdapter()), \
         patch("creator.skills.runner.GEPAEngine") as MockEngine:
        mock_engine_instance = MagicMock()
        mock_engine_instance.run.return_value = iter([])
        mock_engine_instance.top_candidates.return_value = [fake_variant]
        MockEngine.return_value = mock_engine_instance

        result = run_skill(spec, tmp_path)

    assert (tmp_path / "SKILL.md").read_text() == "# testskill\n\nDo great code reviews."
    assert result == fake_variant
