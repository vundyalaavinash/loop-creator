import pytest
from loop_creator.loop_types.registry import get_loop_type, LoopTypeConfig


def test_coding_type_exists():
    lt = get_loop_type("coding")
    assert isinstance(lt, LoopTypeConfig)


def test_all_types_registered():
    for t in ["coding", "debugging", "docs", "rfc", "design", "prompt", "custom"]:
        assert get_loop_type(t) is not None


def test_rubric_injects_goal():
    lt = get_loop_type("coding")
    rubric = lt.rubric("all tests pass")
    assert "all tests pass" in rubric


def test_prompt_type_has_no_judge_cli():
    lt = get_loop_type("prompt")
    assert lt.uses_scorer is True


def test_unknown_type_raises():
    with pytest.raises(KeyError):
        get_loop_type("unknown_xyz")
