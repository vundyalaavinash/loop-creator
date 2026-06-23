import shutil
import yaml
from pathlib import Path
from creator.prompts.spec import PromptSpec


def _prompts_base() -> Path:
    return Path.home() / ".creator" / "prompts"


def prompt_dir(name: str) -> Path:
    return _prompts_base() / name


def save_prompt_spec(spec: PromptSpec) -> None:
    d = prompt_dir(spec.name)
    d.mkdir(parents=True, exist_ok=True)
    (d / "spec.yaml").write_text(yaml.dump(spec.model_dump()))


def load_prompt_spec(name: str) -> PromptSpec:
    data = yaml.safe_load((prompt_dir(name) / "spec.yaml").read_text())
    return PromptSpec(**data)


def list_prompts() -> list[dict]:
    base = _prompts_base()
    if not base.exists():
        return []
    result = []
    for d in sorted(base.iterdir()):
        if d.is_dir() and (d / "spec.yaml").exists():
            stat = (d / "spec.yaml").stat()
            data = yaml.safe_load((d / "spec.yaml").read_text())
            result.append({
                "name": d.name,
                "description_goal": data.get("description_goal", ""),
                "last_modified": stat.st_mtime,
            })
    return result


def delete_prompt(name: str) -> None:
    d = prompt_dir(name)
    if not d.exists():
        raise FileNotFoundError(f"Prompt '{name}' not found")
    shutil.rmtree(d)
