import pytest
from pathlib import Path
from unittest.mock import patch
from creator.prompts.spec import PromptSpec
from creator.prompts.runner import run_prompt, fill_prompt
from creator.spec import GeneratorSpec, JudgeSpec
from creator.adapters.base import LLMAdapter


class StubAdapter(LLMAdapter):
    def call(self, s, u): return "Write commit for {{diff}}."
    def call_structured(self, s, u, schema): return {"score": 0.95, "reason": "great"}
    def is_available(self): return True


def test_prompt_e2e(tmp_path):
    spec = PromptSpec(
        name="e2eprompt",
        description_goal="Generate commit messages",
        variables=["diff"],
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )
    with patch("creator.prompts.runner.build_adapter", return_value=StubAdapter()):
        variant = run_prompt(spec, tmp_path / "e2eprompt")

    output_file = tmp_path / "e2eprompt" / "e2eprompt.md"
    assert output_file.exists()

    with patch("creator.prompts.runner._prompt_output_path", return_value=output_file):
        filled = fill_prompt("e2eprompt", {"diff": "added auth"})
    assert "added auth" in filled
