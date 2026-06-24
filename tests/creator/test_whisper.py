import sys
import pytest
from unittest.mock import MagicMock, patch
from creator.audio.whisper import WhisperTranscriber


def test_local_backend_transcribes(tmp_path):
    fake_model = MagicMock()
    fake_model.transcribe.return_value = (
        [MagicMock(text=" hello world")],
        MagicMock(),
    )
    mock_whisper_module = MagicMock()
    mock_whisper_module.WhisperModel = MagicMock(return_value=fake_model)

    with patch.dict(sys.modules, {"faster_whisper": mock_whisper_module}):
        t = WhisperTranscriber(backend="local", model="base")
        result = t.transcribe(b"fake audio bytes")
    assert result == "hello world"


def test_openai_backend_transcribes():
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = MagicMock(text="hello openai")
    mock_openai_module = MagicMock()
    mock_openai_module.OpenAI = MagicMock(return_value=mock_client)

    with patch.dict(sys.modules, {"openai": mock_openai_module}):
        t = WhisperTranscriber(backend="openai", model="whisper-1", openai_api_key="sk-test")
        result = t.transcribe(b"fake audio bytes")
    assert result == "hello openai"


def test_unknown_backend_raises():
    t = WhisperTranscriber(backend="unknown", model="base")
    with pytest.raises(ValueError, match="Unknown backend"):
        t.transcribe(b"bytes")
