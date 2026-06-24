import httpx
from unittest.mock import MagicMock, patch
from creator.adapters.ollama import OllamaAdapter


def test_call_returns_text():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"message": {"content": "hello"}}
    mock_resp.raise_for_status = MagicMock()
    with patch("creator.adapters.ollama.httpx.post", return_value=mock_resp):
        assert OllamaAdapter().call(system="s", user="u") == "hello"


def test_is_available_true_when_ollama_responds():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("creator.adapters.ollama.httpx.get", return_value=mock_resp):
        assert OllamaAdapter().is_available() is True


def test_is_available_false_on_connection_error():
    with patch("creator.adapters.ollama.httpx.get", side_effect=Exception("refused")):
        assert OllamaAdapter().is_available() is False
