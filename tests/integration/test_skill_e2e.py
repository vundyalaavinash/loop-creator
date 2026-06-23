import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from creator.skills.spec import SkillSpec
from creator.skills.runner import run_skill
from creator.spec import GeneratorSpec, JudgeSpec
from creator.adapters.base import LLMAdapter


class StubAdapter(LLMAdapter):
    def call(self, system, user): return "# myskill\n\nBe a great reviewer."
    def call_structured(self, s, u, schema): return {"score": 0.95, "reason": "excellent"}
    def is_available(self): return True


def test_run_skill_end_to_end(tmp_path):
    spec = SkillSpec(
        name="e2eskill",
        description_goal="Teach Claude to do code review",
        category="code-review",
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )
    events = []
    with patch("creator.runner.build_adapter", return_value=StubAdapter()), \
         patch("creator.skills.runner.build_adapter", return_value=StubAdapter()):
        variant = run_skill(spec, tmp_path / "e2eskill", on_event=events.append)

    assert (tmp_path / "e2eskill" / "SKILL.md").exists()
    assert variant.output.startswith("# myskill")
    assert len(events) > 0
