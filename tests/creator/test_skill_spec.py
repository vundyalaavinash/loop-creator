import pytest
import shutil
from pathlib import Path
from unittest.mock import patch
from creator.skills.spec import (
    SkillSpec, SkillGEPAParams, SKILL_CATEGORIES, SKILL_RUBRICS, get_rubric,
)
from creator.skills.registry import (
    skill_dir, save_skill_spec, load_skill_spec, list_skills, delete_skill, publish_skill,
)
from creator.spec import GeneratorSpec, JudgeSpec


def _make_spec(name="myskill"):
    return SkillSpec(
        name=name,
        description_goal="Perform thorough code review",
        category="code-review",
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )


def test_skill_gepa_defaults():
    p = SkillGEPAParams()
    assert p.population_size == 3
    assert p.max_generations == 5
    assert p.fitness_threshold == 0.90


def test_skill_categories_includes_code_review():
    assert "code-review" in SKILL_CATEGORIES


def test_get_rubric_returns_string_for_known_category():
    r = get_rubric("code-review")
    assert isinstance(r, str) and len(r) > 10


def test_get_rubric_returns_empty_for_custom():
    assert get_rubric("custom") == ""


def test_save_and_load_skill_spec(tmp_path):
    with patch("creator.skills.registry._skills_base", return_value=tmp_path / "skills"):
        spec = _make_spec()
        save_skill_spec(spec)
        loaded = load_skill_spec("myskill")
    assert loaded.name == "myskill"
    assert loaded.category == "code-review"


def test_list_skills(tmp_path):
    with patch("creator.skills.registry._skills_base", return_value=tmp_path / "skills"):
        save_skill_spec(_make_spec("alpha"))
        save_skill_spec(_make_spec("beta"))
        skills = list_skills()
    names = [s["name"] for s in skills]
    assert "alpha" in names and "beta" in names


def test_delete_skill(tmp_path):
    with patch("creator.skills.registry._skills_base", return_value=tmp_path / "skills"):
        save_skill_spec(_make_spec())
        delete_skill("myskill")
        assert not (tmp_path / "skills" / "myskill").exists()


def test_publish_skill(tmp_path):
    skills_base = tmp_path / "skills"
    claude_base = tmp_path / "claude_skills"
    skill_path = skills_base / "myskill"
    skill_path.mkdir(parents=True)
    (skill_path / "SKILL.md").write_text("# myskill\n")
    with patch("creator.skills.registry._skills_base", return_value=skills_base), \
         patch("creator.skills.registry._claude_skills_base", return_value=claude_base):
        dest = publish_skill("myskill")
    assert dest.exists()
    assert dest.read_text() == "# myskill\n"
