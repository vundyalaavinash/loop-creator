import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from creator.prompts.spec import PromptSpec
from creator.prompts.runner import run_prompt, fill_prompt
from creator.spec import GeneratorSpec, JudgeSpec
from creator.adapters.base import LLMAdapter


class FakeAdapter(LLMAdapter):
    def call(self, s, u): return "Write a commit message for {{diff}}."
    def call_structured(self, s, u, schema): return {"score": 0.91, "reason": "good"}
    def is_available(self): return True


def test_run_prompt_writes_md(tmp_path):
    spec = PromptSpec(
        name="commit-msg",
        description_goal="Generate a commit message",
        variables=["diff"],
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )
    with patch("creator.prompts.runner.build_adapter", return_value=FakeAdapter()):
        variant = run_prompt(spec, tmp_path / "commit-msg")
    assert (tmp_path / "commit-msg" / "commit-msg.md").exists()
    assert "{{diff}}" in (tmp_path / "commit-msg" / "commit-msg.md").read_text()


def test_fill_prompt_substitutes_variables(tmp_path):
    md_path = tmp_path / "myprompt.md"
    md_path.write_text("Write a commit message for {{diff}}. Context: {{context}}.")
    with patch("creator.prompts.runner._prompt_output_path", return_value=md_path):
        result = fill_prompt("myprompt", {"diff": "added login", "context": "auth"})
    assert result == "Write a commit message for added login. Context: auth."


def test_fill_prompt_strips_frontmatter(tmp_path):
    md_path = tmp_path / "myprompt.md"
    md_path.write_text("---\nvariables: [diff]\n---\nHello {{diff}}.")
    with patch("creator.prompts.runner._prompt_output_path", return_value=md_path):
        result = fill_prompt("myprompt", {"diff": "world"})
    assert result == "Hello world."
