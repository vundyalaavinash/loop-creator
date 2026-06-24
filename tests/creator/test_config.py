import pytest
from pathlib import Path
from unittest.mock import patch
from creator.config import CreatorConfig, load_config, save_config


def test_load_config_returns_defaults_when_missing(tmp_path):
    with patch("creator.config._config_path", return_value=tmp_path / "config.yaml"):
        cfg = load_config()
    assert cfg.whisper_backend == "local"
    assert cfg.whisper_model == "base"
    assert cfg.openai_api_key == ""


def test_save_and_reload(tmp_path):
    cfg = CreatorConfig(whisper_backend="openai", whisper_model="whisper-1", openai_api_key="sk-test")
    with patch("creator.config._config_path", return_value=tmp_path / "config.yaml"):
        save_config(cfg)
        loaded = load_config()
    assert loaded.whisper_backend == "openai"
    assert loaded.openai_api_key == "sk-test"
