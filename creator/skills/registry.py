import shutil
import yaml
from pathlib import Path
from creator.skills.spec import SkillSpec


def _skills_base() -> Path:
    return Path.home() / ".creator" / "skills"


def _claude_skills_base() -> Path:
    return Path.home() / ".claude" / "skills"


def skill_dir(name: str) -> Path:
    return _skills_base() / name


def save_skill_spec(spec: SkillSpec) -> None:
    d = skill_dir(spec.name)
    d.mkdir(parents=True, exist_ok=True)
    (d / "spec.yaml").write_text(yaml.dump(spec.model_dump()))


def load_skill_spec(name: str) -> SkillSpec:
    data = yaml.safe_load((skill_dir(name) / "spec.yaml").read_text())
    return SkillSpec(**data)


def list_skills() -> list[dict]:
    base = _skills_base()
    if not base.exists():
        return []
    result = []
    for d in sorted(base.iterdir()):
        if d.is_dir() and (d / "spec.yaml").exists():
            stat = (d / "spec.yaml").stat()
            data = yaml.safe_load((d / "spec.yaml").read_text())
            result.append({
                "name": d.name,
                "category": data.get("category", ""),
                "last_modified": stat.st_mtime,
            })
    return result


def delete_skill(name: str) -> None:
    shutil.rmtree(skill_dir(name))


def publish_skill(name: str) -> Path:
    src = skill_dir(name) / "SKILL.md"
    dest_dir = _claude_skills_base() / name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    shutil.copy2(src, dest)
    return dest
