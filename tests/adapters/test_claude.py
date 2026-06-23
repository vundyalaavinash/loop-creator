import shutil
from unittest.mock import MagicMock, patch
from creator.adapters.claude import ClaudeAdapter


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    mock = MagicMock()
    mock.stdout = stdout
    mock.stderr = ""
    mock.returncode = returncode
    return mock


def test_call_returns_text():
    with patch("creator.adapters.claude.subprocess.run", return_value=_mock_run("hello")):
        assert ClaudeAdapter().call(system="sys", user="hi") == "hello"


def test_call_structured_parses_json():
    text = 'Some text {"clarity": 80, "specificity": 70, "hallucination_resistance": 60} more'
    with patch("creator.adapters.claude.subprocess.run", return_value=_mock_run(text)):
        result = ClaudeAdapter().call_structured(system="s", user="u", schema={})
    assert result["clarity"] == 80


def test_call_raises_on_nonzero_exit():
    with patch("creator.adapters.claude.subprocess.run", return_value=_mock_run("", returncode=1)):
        import pytest
        with pytest.raises(RuntimeError, match="claude CLI error"):
            ClaudeAdapter().call(system="s", user="u")


def test_is_available_true_when_claude_on_path():
    with patch("creator.adapters.claude.shutil.which", return_value="/usr/bin/claude"):
        assert ClaudeAdapter().is_available() is True


def test_is_available_false_when_not_on_path():
    with patch("creator.adapters.claude.shutil.which", return_value=None):
        assert ClaudeAdapter().is_available() is False
