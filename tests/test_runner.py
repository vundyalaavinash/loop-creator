from unittest.mock import patch, MagicMock
from loop_creator.runner import build_adapter, detect_available_adapters
from loop_creator.adapters.claude import ClaudeAdapter
from loop_creator.adapters.ollama import OllamaAdapter
from loop_creator.adapters.devin import DevinAdapter


def test_build_adapter_claude():
    a = build_adapter("claude")
    assert isinstance(a, ClaudeAdapter)


def test_build_adapter_ollama():
    a = build_adapter("ollama", model="llama3")
    assert isinstance(a, OllamaAdapter)
    assert a.model == "llama3"


def test_build_adapter_devin():
    a = build_adapter("devin")
    assert isinstance(a, DevinAdapter)


def test_build_adapter_unknown_raises():
    import pytest
    with pytest.raises(ValueError, match="Unknown CLI"):
        build_adapter("unknown_cli_xyz")


def test_detect_available_adapters_returns_list():
    with patch("loop_creator.adapters.claude.shutil.which", return_value="/bin/claude"), \
         patch("loop_creator.adapters.ollama.httpx.get", side_effect=Exception()), \
         patch("loop_creator.adapters.devin.DevinAdapter.is_available", return_value=False):
        result = detect_available_adapters()
    assert isinstance(result, list)
    assert "claude" in result
