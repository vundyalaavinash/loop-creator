import pytest
from pathlib import Path
from unittest.mock import patch
from creator.prompts.spec import PromptSpec, PromptGEPAParams, PROMPT_RUBRICS
from creator.prompts.registry import (
    save_prompt_spec, load_prompt_spec, list_prompts, delete_prompt,
)
from creator.spec import GeneratorSpec, JudgeSpec


def _make_prompt_spec(name="myprompt"):
    return PromptSpec(
        name=name,
        description_goal="Generate a commit message from a diff",
        variables=["diff", "context"],
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )


def test_prompt_gepa_defaults():
    p = PromptGEPAParams()
    assert p.population_size == 3
    assert p.max_generations == 5
    assert p.fitness_threshold == 0.90


def test_prompt_rubrics_is_dict():
    assert isinstance(PROMPT_RUBRICS, dict)
    assert len(PROMPT_RUBRICS) > 0


def test_save_and_load_prompt_spec(tmp_path):
    with patch("creator.prompts.registry._prompts_base", return_value=tmp_path / "prompts"):
        spec = _make_prompt_spec()
        save_prompt_spec(spec)
        loaded = load_prompt_spec("myprompt")
    assert loaded.name == "myprompt"
    assert loaded.variables == ["diff", "context"]


def test_list_prompts(tmp_path):
    with patch("creator.prompts.registry._prompts_base", return_value=tmp_path / "prompts"):
        save_prompt_spec(_make_prompt_spec("a"))
        save_prompt_spec(_make_prompt_spec("b"))
        prompts = list_prompts()
    names = [p["name"] for p in prompts]
    assert "a" in names and "b" in names


def test_delete_prompt(tmp_path):
    with patch("creator.prompts.registry._prompts_base", return_value=tmp_path / "prompts"):
        save_prompt_spec(_make_prompt_spec())
        delete_prompt("myprompt")
        assert not (tmp_path / "prompts" / "myprompt").exists()
