import yaml
from pathlib import Path
from pydantic import BaseModel


class CreatorConfig(BaseModel):
    whisper_backend: str = "local"
    whisper_model: str = "base"
    openai_api_key: str = ""


def _config_path() -> Path:
    return Path.home() / ".creator" / "config.yaml"


def load_config() -> CreatorConfig:
    p = _config_path()
    if not p.exists():
        return CreatorConfig()
    data = yaml.safe_load(p.read_text()) or {}
    return CreatorConfig(**data)


def save_config(config: CreatorConfig) -> None:
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.dump(config.model_dump()))
