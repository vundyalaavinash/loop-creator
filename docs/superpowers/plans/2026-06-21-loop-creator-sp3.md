# Loop Creator SP3: Skill & Prompt Creator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the loop-creator Tauri app with skill and prompt creation workflows, voice input via Whisper transcription, and a settings page — all powered by a renamed `creator/` Python package.

**Architecture:** The existing `loop_creator/` Python package is renamed to `creator/` (with a backward-compatible `lc` CLI alias). Three new artifact types live under `~/.creator/`: loops (existing), skills (SKILL.md files publishable to `~/.claude/skills/`), and prompts (Markdown with `{{variable}}` placeholders). Each artifact type gets its own registry, GEPA runner, FastAPI routes, and React pages. The GEPAEngine gains a `system_prompt` parameter so skill/prompt runners can inject domain-appropriate seed instructions.

**Tech Stack:** Python 3.11+, Pydantic v2, FastAPI, Typer, faster-whisper / OpenAI Whisper API, React 18, TypeScript, Vite, Vitest, Testing Library, React Router v6, Tauri 2.

## Global Constraints

- Package rename: `loop_creator/` → `creator/`; all Python imports change from `loop_creator.` → `creator.`
- Storage migration: `~/.loop-creator/<id>/` → `~/.creator/loops/<id>/`; new dirs: `~/.creator/skills/<name>/`, `~/.creator/prompts/<name>/`, config at `~/.creator/config.yaml`
- CLI entry points: `creator = "creator.cli:app"` and `lc = "creator.cli:app"` (both in pyproject.toml)
- Warp theme tokens: bg-base `#1C1C1C`, bg-surface `#242424`, bg-elevated `#2E2E2E`, accent-teal `#01C7B1`, accent-purple `#9B6DFF`, text-primary `#F0F0F0`, text-muted `#8A8A8A`, border `#383838`
- TDD: write failing test first, run to confirm failure, implement, run to confirm pass, commit
- No placeholders, no TODO items — every step contains the actual code
- YAGNI: implement exactly what is specified, nothing more

---

## File Map

**Rename / modify (Python):**
- `loop_creator/` → `creator/` (all files, all internal imports)
- `pyproject.toml` — name, scripts, packages
- `tauri-app/lc_server/routes/loops.py` — import paths + storage path
- `tauri-app/lc_server/routes/context.py` — import paths
- `tauri-app/lc_server/main.py` — add new routers
- `tauri-app/tests/server/conftest.py` — storage dirs
- `tauri-app/tests/server/test_loops_crud.py` — storage paths
- `tauri-app/tests/server/test_loops_run.py` — import paths + storage paths
- `tests/test_spec.py` — import paths
- `tests/gepa/test_engine.py` — import paths
- `creator/gepa/engine.py` — add `system_prompt` param

**Create (Python):**
- `creator/config.py`
- `creator/audio/__init__.py`
- `creator/audio/whisper.py`
- `creator/audio/recorder.py`
- `creator/skills/__init__.py`
- `creator/skills/spec.py`
- `creator/skills/registry.py`
- `creator/skills/runner.py`
- `creator/prompts/__init__.py`
- `creator/prompts/spec.py`
- `creator/prompts/registry.py`
- `creator/prompts/runner.py`
- `creator/cli.py` (rewrite)
- `tauri-app/lc_server/routes/skills.py`
- `tauri-app/lc_server/routes/prompts.py`
- `tauri-app/lc_server/routes/config.py`
- `tauri-app/lc_server/routes/transcribe.py`

**Create (tests):**
- `tests/creator/test_config.py`
- `tests/creator/test_whisper.py`
- `tests/creator/test_skill_spec.py`
- `tests/creator/test_skill_runner.py`
- `tests/creator/test_prompt_spec.py`
- `tests/creator/test_prompt_runner.py`
- `tests/integration/test_skill_e2e.py`
- `tests/integration/test_prompt_e2e.py`
- `tauri-app/tests/server/test_skills.py`
- `tauri-app/tests/server/test_prompts.py`
- `tauri-app/tests/server/test_config_route.py`
- `tauri-app/tests/server/test_transcribe.py`

**Create (TypeScript):**
- `tauri-app/web/src/types.ts` (modify — add SP3 interfaces)
- `tauri-app/web/src/hooks/useSkill.ts`
- `tauri-app/web/src/hooks/usePrompt.ts`
- `tauri-app/web/src/hooks/useTranscribe.ts`
- `tauri-app/web/src/pages/SkillList.tsx`
- `tauri-app/web/src/pages/SkillBuilder.tsx`
- `tauri-app/web/src/pages/SkillDashboard.tsx`
- `tauri-app/web/src/pages/PromptList.tsx`
- `tauri-app/web/src/pages/PromptBuilder.tsx`
- `tauri-app/web/src/pages/PromptDashboard.tsx`
- `tauri-app/web/src/pages/PromptUse.tsx`
- `tauri-app/web/src/pages/Settings.tsx`
- `tauri-app/web/src/components/Sidebar.tsx` (modify)
- `tauri-app/web/src/App.tsx` (modify)

**Create (React tests):**
- `tauri-app/web/src/hooks/__tests__/useSkill.test.ts`
- `tauri-app/web/src/hooks/__tests__/useTranscribe.test.ts`
- `tauri-app/web/src/pages/__tests__/SkillList.test.tsx`
- `tauri-app/web/src/pages/__tests__/SkillBuilder.test.tsx`
- `tauri-app/web/src/pages/__tests__/SkillDashboard.test.tsx`
- `tauri-app/web/src/pages/__tests__/PromptList.test.tsx`
- `tauri-app/web/src/pages/__tests__/PromptBuilder.test.tsx`
- `tauri-app/web/src/pages/__tests__/PromptDashboard.test.tsx`
- `tauri-app/web/src/pages/__tests__/PromptUse.test.tsx`
- `tauri-app/web/src/pages/__tests__/Settings.test.tsx`

---

### Task 1: Package rename `loop_creator` → `creator`, storage migration

**Files:**
- Rename: `loop_creator/` → `creator/` (directory rename + all internal imports)
- Modify: `pyproject.toml`
- Modify: `tauri-app/lc_server/routes/loops.py`
- Modify: `tauri-app/lc_server/routes/context.py`
- Modify: `tauri-app/tests/server/conftest.py`
- Modify: `tauri-app/tests/server/test_loops_crud.py`
- Modify: `tauri-app/tests/server/test_loops_run.py`
- Modify: `tests/test_spec.py`
- Modify: `tests/gepa/test_engine.py`
- Test: all existing tests pass after rename

**Interfaces:**
- Produces: `creator.*` importable from all downstream tasks; loop storage at `~/.creator/loops/<id>/`

- [ ] **Step 1: Rename the package directory**

```bash
cd /path/to/project
cp -r loop_creator creator
```

Then update every `from loop_creator` and `import loop_creator` inside `creator/` itself:

```bash
find creator/ -name "*.py" -exec sed -i '' 's/from loop_creator\./from creator\./g; s/import loop_creator\./import creator\./g' {} \;
```

- [ ] **Step 2: Run existing tests to confirm they fail with the new import**

```bash
pytest tests/ -x -q 2>&1 | head -30
```
Expected: ImportError or ModuleNotFoundError for `loop_creator`.

- [ ] **Step 3: Update `pyproject.toml`**

Change `name`, `scripts`, and `packages`:

```toml
[project]
name = "creator"

[project.scripts]
creator = "creator.cli:app"
lc = "creator.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["creator"]
```

- [ ] **Step 4: Update `tauri-app/lc_server/routes/loops.py`**

Replace import block:

```python
# FROM:
from loop_creator.spec import LoopSpec, GeneratorSpec, JudgeSpec, ContextSpec, GEPAParams, load_spec, save_spec
from loop_creator.runner import run_loop

# TO:
from creator.spec import LoopSpec, GeneratorSpec, JudgeSpec, ContextSpec, GEPAParams, load_spec, save_spec
from creator.runner import run_loop
```

Replace storage path helper (find `_loop_dir` or equivalent inline path):

```python
# FROM:
def _loop_dir(loop_id: str) -> Path:
    return Path.home() / ".loop-creator" / loop_id

# TO:
def _loop_dir(loop_id: str) -> Path:
    return Path.home() / ".creator" / "loops" / loop_id
```

Also update `list_loops` base path:

```python
# FROM:
base = Path.home() / ".loop-creator"

# TO:
base = Path.home() / ".creator" / "loops"
```

- [ ] **Step 5: Update `tauri-app/lc_server/routes/context.py`**

```python
# FROM:
from loop_creator.context.project import scrape_project
from loop_creator.context.mcp import discover_mcp_servers

# TO:
from creator.context.project import scrape_project
from creator.context.mcp import discover_mcp_servers
```

- [ ] **Step 6: Update `tauri-app/tests/server/conftest.py`**

```python
# FROM:
(tmp_path / ".loop-creator").mkdir()

# TO:
(tmp_path / ".creator" / "loops").mkdir(parents=True)
(tmp_path / ".creator" / "skills").mkdir(parents=True)
(tmp_path / ".creator" / "prompts").mkdir(parents=True)
```

Also update the monkeypatching of the home directory (whatever pattern conftest uses) to point at `tmp_path`.

- [ ] **Step 7: Update `tauri-app/tests/server/test_loops_crud.py`**

```python
# _make_loop helper: FROM:
d = tmp_path / ".loop-creator" / loop_id

# TO:
d = tmp_path / ".creator" / "loops" / loop_id

# test_create_loop assertion: FROM:
loop_dir = tmp_path / ".loop-creator" / "newloop"

# TO:
loop_dir = tmp_path / ".creator" / "loops" / "newloop"

# test_delete_loop assertion: FROM:
assert not (tmp_path / ".loop-creator" / "deleteme").exists()

# TO:
assert not (tmp_path / ".creator" / "loops" / "deleteme").exists()
```

- [ ] **Step 8: Update `tauri-app/tests/server/test_loops_run.py`**

```python
# FROM:
from loop_creator.gepa.engine import GenerationEvent, Variant

# TO:
from creator.gepa.engine import GenerationEvent, Variant

# _make_loop helper: FROM:
d = tmp_path / ".loop-creator" / loop_id

# TO:
d = tmp_path / ".creator" / "loops" / loop_id
```

- [ ] **Step 9: Update `tests/test_spec.py`**

```python
# FROM:
from loop_creator.spec import LoopSpec, GeneratorSpec, JudgeSpec, ContextSpec, GEPAParams, load_spec, save_spec

# TO:
from creator.spec import LoopSpec, GeneratorSpec, JudgeSpec, ContextSpec, GEPAParams, load_spec, save_spec
```

- [ ] **Step 10: Update `tests/gepa/test_engine.py`**

```python
# FROM:
from loop_creator.gepa.engine import GEPAEngine, GenerationEvent, Variant
from loop_creator.gepa.judge import Judge
from loop_creator.gepa.scorer import Scorer
from loop_creator.spec import GEPAParams
from loop_creator.adapters.base import LLMAdapter

# TO:
from creator.gepa.engine import GEPAEngine, GenerationEvent, Variant
from creator.gepa.judge import Judge
from creator.gepa.scorer import Scorer
from creator.spec import GEPAParams
from creator.adapters.base import LLMAdapter
```

Update any other test files under `tests/` that import `loop_creator` the same way.

- [ ] **Step 11: Run all tests to confirm passing**

```bash
pytest tests/ tauri-app/tests/ -q
```
Expected: all tests that passed before still pass.

- [ ] **Step 12: Reinstall the package**

```bash
pip install -e .
```

- [ ] **Step 13: Verify CLI entry points**

```bash
creator --help
lc --help
```
Expected: both show the Typer help without error.

- [ ] **Step 14: Commit**

```bash
git add -A
git commit -m "refactor: rename loop_creator → creator, migrate storage to ~/.creator/loops/"
```

---

### Task 2: `creator/config.py` — app-level config

**Files:**
- Create: `creator/config.py`
- Create: `tests/creator/__init__.py`
- Create: `tests/creator/test_config.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `CreatorConfig(BaseModel)` with fields: `whisper_backend: str = "local"`, `whisper_model: str = "base"`, `openai_api_key: str = ""`
  - `load_config() -> CreatorConfig` — reads `~/.creator/config.yaml`, returns defaults if missing
  - `save_config(config: CreatorConfig) -> None` — writes to `~/.creator/config.yaml`

- [ ] **Step 1: Write the failing test**

```python
# tests/creator/test_config.py
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
```

- [ ] **Step 2: Run test to confirm failure**

```bash
pytest tests/creator/test_config.py -v
```
Expected: FAIL — `creator.config` does not exist.

- [ ] **Step 3: Implement `creator/config.py`**

```python
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
```

- [ ] **Step 4: Run test to confirm passing**

```bash
pytest tests/creator/test_config.py -v
```
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add creator/config.py tests/creator/__init__.py tests/creator/test_config.py
git commit -m "feat(sp3): CreatorConfig with load/save"
```

---

### Task 3: `creator/audio/` — Whisper transcription + recorder

**Files:**
- Create: `creator/audio/__init__.py`
- Create: `creator/audio/whisper.py`
- Create: `creator/audio/recorder.py`
- Create: `tests/creator/test_whisper.py`

**Interfaces:**
- Consumes: `CreatorConfig` from Task 2
- Produces:
  - `WhisperTranscriber(backend: str, model: str, openai_api_key: str = "")` with `.transcribe(audio_bytes: bytes) -> str`
  - `record_audio() -> bytes` — records from mic via sounddevice until Enter pressed

- [ ] **Step 1: Write the failing test**

```python
# tests/creator/test_whisper.py
import pytest
from unittest.mock import MagicMock, patch
from creator.audio.whisper import WhisperTranscriber


def test_local_backend_transcribes(tmp_path):
    fake_model = MagicMock()
    fake_model.transcribe.return_value = (
        [MagicMock(text=" hello world")],
        MagicMock(),
    )
    with patch("creator.audio.whisper.WhisperModel", return_value=fake_model):
        t = WhisperTranscriber(backend="local", model="base")
        result = t.transcribe(b"fake audio bytes")
    assert result == "hello world"


def test_openai_backend_transcribes():
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = MagicMock(text="hello openai")
    with patch("creator.audio.whisper.OpenAI", return_value=mock_client):
        t = WhisperTranscriber(backend="openai", model="whisper-1", openai_api_key="sk-test")
        result = t.transcribe(b"fake audio bytes")
    assert result == "hello openai"


def test_unknown_backend_raises():
    t = WhisperTranscriber(backend="unknown", model="base")
    with pytest.raises(ValueError, match="Unknown backend"):
        t.transcribe(b"bytes")
```

- [ ] **Step 2: Run test to confirm failure**

```bash
pytest tests/creator/test_whisper.py -v
```
Expected: FAIL — `creator.audio.whisper` does not exist.

- [ ] **Step 3: Implement `creator/audio/whisper.py`**

```python
import io
from typing import TYPE_CHECKING


class WhisperTranscriber:
    def __init__(self, backend: str, model: str, openai_api_key: str = ""):
        self.backend = backend
        self.model = model
        self.openai_api_key = openai_api_key

    def transcribe(self, audio_bytes: bytes) -> str:
        if self.backend == "local":
            return self._transcribe_local(audio_bytes)
        if self.backend == "openai":
            return self._transcribe_openai(audio_bytes)
        raise ValueError(f"Unknown backend: {self.backend!r}")

    def _transcribe_local(self, audio_bytes: bytes) -> str:
        from faster_whisper import WhisperModel
        model = WhisperModel(self.model)
        segments, _ = model.transcribe(io.BytesIO(audio_bytes))
        return "".join(s.text for s in segments).strip()

    def _transcribe_openai(self, audio_bytes: bytes) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_api_key)
        result = client.audio.transcriptions.create(
            model=self.model,
            file=("audio.wav", audio_bytes, "audio/wav"),
        )
        return result.text
```

- [ ] **Step 4: Implement `creator/audio/recorder.py`**

```python
def record_audio() -> bytes:
    import sounddevice as sd
    import numpy as np
    import wave, io

    sample_rate = 16000
    print("Recording... press Enter to stop.")
    chunks = []

    def callback(indata, frames, time, status):
        chunks.append(indata.copy())

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16", callback=callback):
        input()

    audio = np.concatenate(chunks, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()
```

- [ ] **Step 5: Create `creator/audio/__init__.py`**

```python
```
(empty file)

- [ ] **Step 6: Run tests to confirm passing**

```bash
pytest tests/creator/test_whisper.py -v
```
Expected: PASS (3 tests).

- [ ] **Step 7: Commit**

```bash
git add creator/audio/ tests/creator/test_whisper.py
git commit -m "feat(sp3): WhisperTranscriber with local/openai backends"
```

---

### Task 4: `creator/skills/spec.py` + `creator/skills/registry.py`

**Files:**
- Create: `creator/skills/__init__.py`
- Create: `creator/skills/spec.py`
- Create: `creator/skills/registry.py`
- Create: `tests/creator/test_skill_spec.py`

**Interfaces:**
- Consumes: `GeneratorSpec`, `JudgeSpec` from `creator.spec` (Task 1)
- Produces:
  - `SkillGEPAParams(BaseModel)`: `population_size=3`, `max_generations=5`, `fitness_threshold=0.90`
  - `SkillSpec(BaseModel)`: `name`, `description_goal`, `category`, `target_platforms`, `generator`, `judge`, `gepa`
  - `SKILL_CATEGORIES: list[str]`
  - `SKILL_RUBRICS: dict[str, str]`
  - `get_rubric(category: str) -> str`
  - `skill_dir(name: str) -> Path` — `~/.creator/skills/<name>/`
  - `save_skill_spec(spec: SkillSpec) -> None`
  - `load_skill_spec(name: str) -> SkillSpec`
  - `list_skills() -> list[dict]` — `[{name, category, last_modified}]`
  - `delete_skill(name: str) -> None`
  - `publish_skill(name: str) -> Path` — copies SKILL.md to `~/.claude/skills/<name>/SKILL.md`

- [ ] **Step 1: Write the failing tests**

```python
# tests/creator/test_skill_spec.py
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/creator/test_skill_spec.py -v
```
Expected: FAIL — modules do not exist.

- [ ] **Step 3: Implement `creator/skills/spec.py`**

```python
from typing import Literal
from pydantic import BaseModel, Field
from creator.spec import GeneratorSpec, JudgeSpec

SKILL_CATEGORIES = ["code-review", "testing", "documentation", "devops", "data-analysis", "custom"]

SKILL_RUBRICS: dict[str, str] = {
    "code-review": (
        "The skill teaches Claude to perform thorough, actionable code review with a low "
        "false-positive rate. Evaluate: does it catch real bugs, does it suggest concrete fixes, "
        "does it avoid nitpicking stylistic preferences, is the tone constructive?"
    ),
    "testing": (
        "The skill teaches Claude to write high-quality tests. Evaluate coverage completeness, "
        "test independence, descriptive failure messages, and avoidance of implementation details."
    ),
    "documentation": (
        "The skill teaches Claude to write clear documentation. Evaluate clarity, completeness, "
        "correct examples, appropriate audience level, and scannable structure."
    ),
    "devops": (
        "The skill teaches Claude to write safe infrastructure scripts. Evaluate safety, "
        "idempotency, rollback awareness, and least-privilege principle."
    ),
    "data-analysis": (
        "The skill teaches Claude to perform rigorous data analysis. Evaluate correctness, "
        "insight quality, reproducibility, and appropriate statistical methods."
    ),
    "custom": "",
}


def get_rubric(category: str) -> str:
    return SKILL_RUBRICS.get(category, "")


class SkillGEPAParams(BaseModel):
    population_size: int = 3
    max_generations: int = 5
    fitness_threshold: float = 0.90


class SkillSpec(BaseModel):
    name: str
    description_goal: str
    category: str
    target_platforms: list[str] = Field(default_factory=lambda: ["claude-code"])
    generator: GeneratorSpec = Field(default_factory=GeneratorSpec)
    judge: JudgeSpec = Field(default_factory=JudgeSpec)
    gepa: SkillGEPAParams = Field(default_factory=SkillGEPAParams)
```

- [ ] **Step 4: Implement `creator/skills/registry.py`**

```python
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
```

- [ ] **Step 5: Create `creator/skills/__init__.py`**

```python
```
(empty)

- [ ] **Step 6: Run tests to confirm passing**

```bash
pytest tests/creator/test_skill_spec.py -v
```
Expected: PASS (8 tests).

- [ ] **Step 7: Commit**

```bash
git add creator/skills/ tests/creator/test_skill_spec.py
git commit -m "feat(sp3): SkillSpec, SkillGEPAParams, skill registry"
```

---

### Task 5: `creator/skills/runner.py` + GEPAEngine `system_prompt` param

**Files:**
- Modify: `creator/gepa/engine.py` — add `system_prompt: str = SEED_SYSTEM` param
- Create: `creator/skills/runner.py`
- Create: `tests/creator/test_skill_runner.py`
- Create: `tests/integration/test_skill_e2e.py`

**Interfaces:**
- Consumes: `GEPAEngine` from `creator.gepa.engine`, `SkillSpec` from Task 4, `GEPAParams` from `creator.spec`, `build_adapter` from `creator.runner`
- Produces:
  - `run_skill(spec: SkillSpec, skill_dir: Path, on_event=None) -> Variant`
  - Modified `GEPAEngine.__init__(self, generator, judge, params, scorer=None, low_score_callback=None, system_prompt: str = SEED_SYSTEM)`

- [ ] **Step 1: Write the failing test for GEPAEngine system_prompt**

```python
# tests/creator/test_skill_runner.py
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from creator.gepa.engine import GEPAEngine, SEED_SYSTEM
from creator.spec import GEPAParams
from creator.adapters.base import LLMAdapter


class FakeAdapter(LLMAdapter):
    def __init__(self, output="result"):
        self._output = output
    def call(self, system, user): return self._output
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


class FakeJudge:
    def score(self, output, rubric): return (0.9, "good")


def test_engine_accepts_system_prompt():
    params = GEPAParams(population_size=2, max_generations=1, fitness_threshold=0.99)
    engine = GEPAEngine(
        generator=FakeAdapter(),
        judge=FakeJudge(),
        params=params,
        system_prompt="Custom system prompt",
    )
    assert engine.system_prompt == "Custom system prompt"


def test_engine_default_system_prompt():
    params = GEPAParams(population_size=2, max_generations=1, fitness_threshold=0.99)
    engine = GEPAEngine(generator=FakeAdapter(), judge=FakeJudge(), params=params)
    assert engine.system_prompt == SEED_SYSTEM


def test_run_skill_writes_skill_md(tmp_path):
    from creator.skills.spec import SkillSpec
    from creator.skills.runner import run_skill
    from creator.spec import GeneratorSpec, JudgeSpec

    spec = SkillSpec(
        name="testskill",
        description_goal="Write great code reviews",
        category="code-review",
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )

    fake_variant = MagicMock()
    fake_variant.output = "# testskill\n\nDo great code reviews."

    with patch("creator.skills.runner.build_adapter", return_value=FakeAdapter()), \
         patch("creator.skills.runner.GEPAEngine") as MockEngine:
        mock_engine_instance = MagicMock()
        mock_engine_instance.run.return_value = iter([])
        mock_engine_instance.top_candidates.return_value = [fake_variant]
        MockEngine.return_value = mock_engine_instance

        result = run_skill(spec, tmp_path)

    assert (tmp_path / "SKILL.md").read_text() == "# testskill\n\nDo great code reviews."
    assert result == fake_variant
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/creator/test_skill_runner.py -v
```
Expected: FAIL.

- [ ] **Step 3: Modify `creator/gepa/engine.py` to add `system_prompt` param**

Find the `GEPAEngine.__init__` signature and add the param:

```python
# In creator/gepa/engine.py, change __init__ from:
def __init__(self, generator, judge, params: GEPAParams, scorer=None, low_score_callback=None):
    self.generator = generator
    self.judge = judge
    self.params = params
    self.scorer = scorer
    self.low_score_callback = low_score_callback
    ...

# TO:
def __init__(self, generator, judge, params: GEPAParams, scorer=None, low_score_callback=None,
             system_prompt: str = SEED_SYSTEM):
    self.generator = generator
    self.judge = judge
    self.params = params
    self.scorer = scorer
    self.low_score_callback = low_score_callback
    self.system_prompt = system_prompt
    ...
```

Then replace all occurrences of `self.generator.call(SEED_SYSTEM, ...)` with `self.generator.call(self.system_prompt, ...)` throughout engine.py.

- [ ] **Step 4: Implement `creator/skills/runner.py`**

```python
from pathlib import Path
from creator.gepa.engine import GEPAEngine, Variant
from creator.gepa.judge import Judge
from creator.skills.spec import SkillSpec, get_rubric
from creator.spec import GEPAParams
from creator.runner import build_adapter

SEED_SYSTEM_SKILL = (
    "You are an expert at writing Claude Code skills. "
    "Output only the SKILL.md content — no preamble or explanation."
)


def run_skill(spec: SkillSpec, skill_dir: Path, on_event=None) -> Variant:
    generator = build_adapter(spec.generator.cli, spec.generator.model)
    judge_adapter = build_adapter(spec.judge.cli, spec.judge.model)

    rubric = get_rubric(spec.category) or spec.judge.rubric or ""
    judge = Judge(adapter=judge_adapter, rubric=rubric)

    params = GEPAParams(
        population_size=spec.gepa.population_size,
        top_k=2,
        max_generations=spec.gepa.max_generations,
        fitness_threshold=spec.gepa.fitness_threshold,
        stagnation_limit=3,
        mutation_operators=["rephrase", "expand", "constrain", "crossover"],
    )

    engine = GEPAEngine(
        generator=generator,
        judge=judge,
        params=params,
        system_prompt=SEED_SYSTEM_SKILL,
    )

    for event in engine.run(task=spec.description_goal, goal=rubric or spec.description_goal):
        if on_event:
            on_event(event)

    best = engine.top_candidates(1)[0]
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(best.output)
    return best
```

- [ ] **Step 5: Run tests to confirm passing**

```bash
pytest tests/creator/test_skill_runner.py -v
```
Expected: PASS (3 tests).

- [ ] **Step 6: Confirm existing engine tests still pass**

```bash
pytest tests/gepa/test_engine.py -v
```
Expected: all green (system_prompt param is backward-compatible).

- [ ] **Step 7: Write integration test**

```python
# tests/integration/test_skill_e2e.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from creator.skills.spec import SkillSpec
from creator.skills.runner import run_skill
from creator.spec import GeneratorSpec, JudgeSpec
from creator.adapters.base import LLMAdapter


class StubAdapter(LLMAdapter):
    def call(self, system, user): return "# myskill\n\nBe a great reviewer."
    def call_structured(self, s, u, schema): return {"score": 0.95, "reason": "excellent"}
    def is_available(self): return True


def test_run_skill_end_to_end(tmp_path):
    spec = SkillSpec(
        name="e2eskill",
        description_goal="Teach Claude to do code review",
        category="code-review",
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )
    events = []
    with patch("creator.runner.build_adapter", return_value=StubAdapter()), \
         patch("creator.skills.runner.build_adapter", return_value=StubAdapter()):
        variant = run_skill(spec, tmp_path / "e2eskill", on_event=events.append)

    assert (tmp_path / "e2eskill" / "SKILL.md").exists()
    assert variant.output.startswith("# myskill")
    assert len(events) > 0
```

- [ ] **Step 8: Run integration test**

```bash
pytest tests/integration/test_skill_e2e.py -v
```
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add creator/gepa/engine.py creator/skills/runner.py tests/creator/test_skill_runner.py tests/integration/test_skill_e2e.py tests/integration/__init__.py
git commit -m "feat(sp3): skill runner + GEPAEngine system_prompt param"
```

---

### Task 6: `creator/prompts/spec.py` + `creator/prompts/registry.py`

**Files:**
- Create: `creator/prompts/__init__.py`
- Create: `creator/prompts/spec.py`
- Create: `creator/prompts/registry.py`
- Create: `tests/creator/test_prompt_spec.py`

**Interfaces:**
- Consumes: `GeneratorSpec`, `JudgeSpec` from `creator.spec`
- Produces:
  - `PromptGEPAParams(BaseModel)`: `population_size=3`, `max_generations=5`, `fitness_threshold=0.90`
  - `PromptSpec(BaseModel)`: `name`, `description_goal`, `variables: list[str]`, `generator`, `judge`, `gepa`
  - `PROMPT_RUBRICS: dict[str, str]`
  - `prompt_dir(name: str) -> Path` — `~/.creator/prompts/<name>/`
  - `save_prompt_spec(spec: PromptSpec) -> None`
  - `load_prompt_spec(name: str) -> PromptSpec`
  - `list_prompts() -> list[dict]`
  - `delete_prompt(name: str) -> None`

- [ ] **Step 1: Write the failing tests**

```python
# tests/creator/test_prompt_spec.py
import pytest
from pathlib import Path
from unittest.mock import patch
from creator.prompts.spec import PromptSpec, PromptGEPAParams, PROMPT_RUBRICS
from creator.prompts.registry import (
    save_prompt_spec, load_prompt_spec, list_prompts, delete_prompt,
)
from creator.spec import GeneratorSpec, JudgeSpec


def _make_prompt_spec(name="myprompt"):
    return PromptSpec(
        name=name,
        description_goal="Generate a commit message from a diff",
        variables=["diff", "context"],
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )


def test_prompt_gepa_defaults():
    p = PromptGEPAParams()
    assert p.population_size == 3
    assert p.max_generations == 5
    assert p.fitness_threshold == 0.90


def test_prompt_rubrics_is_dict():
    assert isinstance(PROMPT_RUBRICS, dict)
    assert len(PROMPT_RUBRICS) > 0


def test_save_and_load_prompt_spec(tmp_path):
    with patch("creator.prompts.registry._prompts_base", return_value=tmp_path / "prompts"):
        spec = _make_prompt_spec()
        save_prompt_spec(spec)
        loaded = load_prompt_spec("myprompt")
    assert loaded.name == "myprompt"
    assert loaded.variables == ["diff", "context"]


def test_list_prompts(tmp_path):
    with patch("creator.prompts.registry._prompts_base", return_value=tmp_path / "prompts"):
        save_prompt_spec(_make_prompt_spec("a"))
        save_prompt_spec(_make_prompt_spec("b"))
        prompts = list_prompts()
    names = [p["name"] for p in prompts]
    assert "a" in names and "b" in names


def test_delete_prompt(tmp_path):
    with patch("creator.prompts.registry._prompts_base", return_value=tmp_path / "prompts"):
        save_prompt_spec(_make_prompt_spec())
        delete_prompt("myprompt")
        assert not (tmp_path / "prompts" / "myprompt").exists()
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/creator/test_prompt_spec.py -v
```
Expected: FAIL.

- [ ] **Step 3: Implement `creator/prompts/spec.py`**

```python
from pydantic import BaseModel, Field
from creator.spec import GeneratorSpec, JudgeSpec

PROMPT_RUBRICS: dict[str, str] = {
    "commit-message": (
        "The prompt produces clear, conventional commit messages. Evaluate: does it follow "
        "Conventional Commits format, is the subject line under 72 chars, does the body explain why?"
    ),
    "pr-description": (
        "The prompt produces complete PR descriptions. Evaluate: does it summarize the change, "
        "list testing steps, note any breaking changes?"
    ),
    "code-explanation": (
        "The prompt explains code clearly to the target audience. Evaluate: correct abstraction level, "
        "no jargon without definition, concrete examples."
    ),
    "custom": "",
}


class PromptGEPAParams(BaseModel):
    population_size: int = 3
    max_generations: int = 5
    fitness_threshold: float = 0.90


class PromptSpec(BaseModel):
    name: str
    description_goal: str
    variables: list[str] = Field(default_factory=list)
    generator: GeneratorSpec = Field(default_factory=GeneratorSpec)
    judge: JudgeSpec = Field(default_factory=JudgeSpec)
    gepa: PromptGEPAParams = Field(default_factory=PromptGEPAParams)
```

- [ ] **Step 4: Implement `creator/prompts/registry.py`**

```python
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
    shutil.rmtree(prompt_dir(name))
```

- [ ] **Step 5: Create `creator/prompts/__init__.py`** (empty)

- [ ] **Step 6: Run tests to confirm passing**

```bash
pytest tests/creator/test_prompt_spec.py -v
```
Expected: PASS (5 tests).

- [ ] **Step 7: Commit**

```bash
git add creator/prompts/ tests/creator/test_prompt_spec.py
git commit -m "feat(sp3): PromptSpec, PromptGEPAParams, prompt registry"
```

---

### Task 7: `creator/prompts/runner.py` — run + fill

**Files:**
- Create: `creator/prompts/runner.py`
- Create: `tests/creator/test_prompt_runner.py`
- Create: `tests/integration/test_prompt_e2e.py`

**Interfaces:**
- Consumes: `PromptSpec` (Task 6), `GEPAEngine` (Task 5), `build_adapter` from `creator.runner`
- Produces:
  - `run_prompt(spec: PromptSpec, prompt_dir: Path, on_event=None) -> Variant`
  - `fill_prompt(name: str, variables: dict[str, str]) -> str` — strips YAML frontmatter, replaces `{{key}}`

- [ ] **Step 1: Write the failing tests**

```python
# tests/creator/test_prompt_runner.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from creator.prompts.spec import PromptSpec
from creator.prompts.runner import run_prompt, fill_prompt
from creator.spec import GeneratorSpec, JudgeSpec
from creator.adapters.base import LLMAdapter


class FakeAdapter(LLMAdapter):
    def call(self, s, u): return "Write a commit message for {{diff}}."
    def call_structured(self, s, u, schema): return {"score": 0.91, "reason": "good"}
    def is_available(self): return True


def test_run_prompt_writes_md(tmp_path):
    spec = PromptSpec(
        name="commit-msg",
        description_goal="Generate a commit message",
        variables=["diff"],
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )
    with patch("creator.prompts.runner.build_adapter", return_value=FakeAdapter()):
        variant = run_prompt(spec, tmp_path / "commit-msg")
    assert (tmp_path / "commit-msg" / "commit-msg.md").exists()
    assert "{{diff}}" in (tmp_path / "commit-msg" / "commit-msg.md").read_text()


def test_fill_prompt_substitutes_variables(tmp_path):
    md_path = tmp_path / "myprompt.md"
    md_path.write_text("Write a commit message for {{diff}}. Context: {{context}}.")
    with patch("creator.prompts.runner._prompt_output_path", return_value=md_path):
        result = fill_prompt("myprompt", {"diff": "added login", "context": "auth"})
    assert result == "Write a commit message for added login. Context: auth."


def test_fill_prompt_strips_frontmatter(tmp_path):
    md_path = tmp_path / "myprompt.md"
    md_path.write_text("---\nvariables: [diff]\n---\nHello {{diff}}.")
    with patch("creator.prompts.runner._prompt_output_path", return_value=md_path):
        result = fill_prompt("myprompt", {"diff": "world"})
    assert result == "Hello world."
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/creator/test_prompt_runner.py -v
```
Expected: FAIL.

- [ ] **Step 3: Implement `creator/prompts/runner.py`**

```python
from pathlib import Path
from creator.gepa.engine import GEPAEngine, Variant
from creator.gepa.judge import Judge
from creator.prompts.spec import PromptSpec, PROMPT_RUBRICS
from creator.prompts.registry import prompt_dir as _get_prompt_dir
from creator.spec import GEPAParams
from creator.runner import build_adapter

SEED_SYSTEM_PROMPT = (
    "You are an expert prompt engineer. "
    "Output only the prompt body — no preamble. Use {{variable}} syntax for placeholders."
)


def _prompt_output_path(name: str) -> Path:
    return _get_prompt_dir(name) / f"{name}.md"


def run_prompt(spec: PromptSpec, prompt_dir: Path, on_event=None) -> Variant:
    generator = build_adapter(spec.generator.cli, spec.generator.model)
    judge_adapter = build_adapter(spec.judge.cli, spec.judge.model)

    rubric = PROMPT_RUBRICS.get(spec.judge.rubric or "", "") or spec.judge.rubric or spec.description_goal
    judge = Judge(adapter=judge_adapter, rubric=rubric)

    params = GEPAParams(
        population_size=spec.gepa.population_size,
        top_k=2,
        max_generations=spec.gepa.max_generations,
        fitness_threshold=spec.gepa.fitness_threshold,
        stagnation_limit=3,
        mutation_operators=["rephrase", "expand", "constrain", "crossover"],
    )

    engine = GEPAEngine(
        generator=generator,
        judge=judge,
        params=params,
        system_prompt=SEED_SYSTEM_PROMPT,
    )

    for event in engine.run(task=spec.description_goal, goal=rubric):
        if on_event:
            on_event(event)

    best = engine.top_candidates(1)[0]
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / f"{spec.name}.md").write_text(best.output)
    return best


def fill_prompt(name: str, variables: dict[str, str]) -> str:
    template = _prompt_output_path(name).read_text()
    if template.startswith("---"):
        end = template.find("---", 3)
        template = template[end + 3:].lstrip("\n")
    for key, val in variables.items():
        template = template.replace(f"{{{{{key}}}}}", val)
    return template
```

- [ ] **Step 4: Run tests to confirm passing**

```bash
pytest tests/creator/test_prompt_runner.py -v
```
Expected: PASS (3 tests).

- [ ] **Step 5: Write integration test**

```python
# tests/integration/test_prompt_e2e.py
import pytest
from pathlib import Path
from unittest.mock import patch
from creator.prompts.spec import PromptSpec
from creator.prompts.runner import run_prompt, fill_prompt
from creator.spec import GeneratorSpec, JudgeSpec
from creator.adapters.base import LLMAdapter


class StubAdapter(LLMAdapter):
    def call(self, s, u): return "Write commit for {{diff}}."
    def call_structured(self, s, u, schema): return {"score": 0.95, "reason": "great"}
    def is_available(self): return True


def test_prompt_e2e(tmp_path):
    spec = PromptSpec(
        name="e2eprompt",
        description_goal="Generate commit messages",
        variables=["diff"],
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )
    with patch("creator.prompts.runner.build_adapter", return_value=StubAdapter()):
        variant = run_prompt(spec, tmp_path / "e2eprompt")

    output_file = tmp_path / "e2eprompt" / "e2eprompt.md"
    assert output_file.exists()

    with patch("creator.prompts.runner._prompt_output_path", return_value=output_file):
        filled = fill_prompt("e2eprompt", {"diff": "added auth"})
    assert "added auth" in filled
```

- [ ] **Step 6: Run integration test**

```bash
pytest tests/integration/test_prompt_e2e.py -v
```
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add creator/prompts/runner.py tests/creator/test_prompt_runner.py tests/integration/test_prompt_e2e.py
git commit -m "feat(sp3): prompt runner with fill_prompt variable substitution"
```

---

### Task 8: Rewrite `creator/cli.py` with skill/prompt sub-apps + `--voice`

**Files:**
- Modify: `creator/cli.py`

**Interfaces:**
- Consumes: `run_skill` (Task 5), `run_prompt` (Task 7), `fill_prompt` (Task 7), `save_skill_spec` / `load_skill_spec` / `list_skills` / `delete_skill` / `publish_skill` (Task 4), `save_prompt_spec` / `load_prompt_spec` / `list_prompts` / `delete_prompt` (Task 6), `load_config` / `save_config` / `CreatorConfig` (Task 2), `WhisperTranscriber` (Task 3), `record_audio` (Task 3)
- Produces: `creator` and `lc` CLI commands with `loop`, `skill`, and `prompt` sub-apps; `--voice` flag on run commands

- [ ] **Step 1: Verify existing CLI tests pass (baseline)**

```bash
pytest tests/ -k "cli" -v
```
Note the passing tests — they must still pass after rewrite.

- [ ] **Step 2: Implement the rewritten `creator/cli.py`**

```python
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Creator — evolve loops, skills, and prompts with GEPA")
loop_app = typer.Typer(help="Manage and run loops")
skill_app = typer.Typer(help="Manage and run skills")
prompt_app = typer.Typer(help="Manage and run prompts")

app.add_typer(loop_app, name="loop")
app.add_typer(skill_app, name="skill")
app.add_typer(prompt_app, name="prompt")


# ── Loop commands (thin wrappers preserving SP1 behavior) ──────────────────

@loop_app.command("run")
def loop_run(loop_id: str, voice: bool = typer.Option(False, "--voice", help="Transcribe task from mic")):
    from creator.runner import run_loop
    from creator.spec import load_spec
    from creator.skills.registry import skill_dir  # reuse Path.home()/.creator pattern
    loop_dir = Path.home() / ".creator" / "loops" / loop_id
    spec = load_spec(str(loop_dir / "spec.yaml"))
    if voice:
        task = _transcribe_from_mic()
        spec.task = task
    for event in _stream_run(lambda cb: run_loop(spec, loop_dir, on_event=cb)):
        typer.echo(f"[gen {event.generation}] best={event.best_score:.2f}")


@loop_app.command("list")
def loop_list():
    from creator.skills.registry import list_skills  # reuse pattern
    base = Path.home() / ".creator" / "loops"
    if not base.exists():
        typer.echo("No loops yet.")
        return
    for d in sorted(base.iterdir()):
        if d.is_dir():
            typer.echo(d.name)


# ── Skill commands ─────────────────────────────────────────────────────────

@skill_app.command("new")
def skill_new(
    name: str,
    description: str = typer.Option(..., "--description", "-d"),
    category: str = typer.Option("custom", "--category", "-c"),
):
    from creator.skills.spec import SkillSpec
    from creator.skills.registry import save_skill_spec
    from creator.spec import GeneratorSpec, JudgeSpec
    spec = SkillSpec(
        name=name, description_goal=description, category=category,
        generator=GeneratorSpec(cli="claude"), judge=JudgeSpec(cli="claude"),
    )
    save_skill_spec(spec)
    typer.echo(f"Skill '{name}' created.")


@skill_app.command("run")
def skill_run(name: str, voice: bool = typer.Option(False, "--voice")):
    from creator.skills.spec import SkillSpec
    from creator.skills.registry import load_skill_spec, skill_dir
    from creator.skills.runner import run_skill
    spec = load_skill_spec(name)
    if voice:
        spec.description_goal = _transcribe_from_mic()
    d = skill_dir(name)
    events = []
    variant = run_skill(spec, d, on_event=lambda e: typer.echo(f"[gen {e.generation}] best={e.best_score:.2f}"))
    typer.echo(f"\nDone. Best score: {variant.score:.2f}")
    typer.echo((d / "SKILL.md").read_text())


@skill_app.command("list")
def skill_list():
    from creator.skills.registry import list_skills
    skills = list_skills()
    if not skills:
        typer.echo("No skills yet.")
        return
    for s in skills:
        typer.echo(f"{s['name']}  ({s['category']})")


@skill_app.command("delete")
def skill_delete(name: str):
    from creator.skills.registry import delete_skill
    delete_skill(name)
    typer.echo(f"Deleted skill '{name}'.")


@skill_app.command("publish")
def skill_publish(name: str):
    from creator.skills.registry import publish_skill
    dest = publish_skill(name)
    typer.echo(f"Published to {dest}")


# ── Prompt commands ────────────────────────────────────────────────────────

@prompt_app.command("new")
def prompt_new(
    name: str,
    description: str = typer.Option(..., "--description", "-d"),
    variables: str = typer.Option("", "--variables", "-v", help="Comma-separated variable names"),
):
    from creator.prompts.spec import PromptSpec
    from creator.prompts.registry import save_prompt_spec
    from creator.spec import GeneratorSpec, JudgeSpec
    var_list = [v.strip() for v in variables.split(",") if v.strip()]
    spec = PromptSpec(
        name=name, description_goal=description, variables=var_list,
        generator=GeneratorSpec(cli="claude"), judge=JudgeSpec(cli="claude"),
    )
    save_prompt_spec(spec)
    typer.echo(f"Prompt '{name}' created.")


@prompt_app.command("run")
def prompt_run(name: str, voice: bool = typer.Option(False, "--voice")):
    from creator.prompts.registry import load_prompt_spec, prompt_dir
    from creator.prompts.runner import run_prompt
    spec = load_prompt_spec(name)
    if voice:
        spec.description_goal = _transcribe_from_mic()
    d = prompt_dir(name)
    variant = run_prompt(spec, d, on_event=lambda e: typer.echo(f"[gen {e.generation}] best={e.best_score:.2f}"))
    typer.echo(f"\nDone. Best score: {variant.score:.2f}")


@prompt_app.command("use")
def prompt_use(name: str, variables: list[str] = typer.Argument(None, help="key=value pairs")):
    from creator.prompts.runner import fill_prompt
    var_dict = {}
    for item in (variables or []):
        k, _, v = item.partition("=")
        var_dict[k] = v
    result = fill_prompt(name, var_dict)
    typer.echo(result)


@prompt_app.command("list")
def prompt_list():
    from creator.prompts.registry import list_prompts
    prompts = list_prompts()
    if not prompts:
        typer.echo("No prompts yet.")
        return
    for p in prompts:
        typer.echo(f"{p['name']}  — {p['description_goal'][:60]}")


@prompt_app.command("delete")
def prompt_delete(name: str):
    from creator.prompts.registry import delete_prompt
    delete_prompt(name)
    typer.echo(f"Deleted prompt '{name}'.")


# ── Config command ─────────────────────────────────────────────────────────

@app.command("config")
def config_cmd(
    whisper_backend: Optional[str] = typer.Option(None),
    whisper_model: Optional[str] = typer.Option(None),
    openai_api_key: Optional[str] = typer.Option(None),
):
    from creator.config import load_config, save_config
    cfg = load_config()
    if whisper_backend:
        cfg.whisper_backend = whisper_backend
    if whisper_model:
        cfg.whisper_model = whisper_model
    if openai_api_key:
        cfg.openai_api_key = openai_api_key
    save_config(cfg)
    typer.echo(f"Config saved: backend={cfg.whisper_backend} model={cfg.whisper_model}")


# ── Helpers ────────────────────────────────────────────────────────────────

def _transcribe_from_mic() -> str:
    from creator.audio.recorder import record_audio
    from creator.audio.whisper import WhisperTranscriber
    from creator.config import load_config
    cfg = load_config()
    typer.echo("Recording... press Enter to stop.")
    audio = record_audio()
    t = WhisperTranscriber(backend=cfg.whisper_backend, model=cfg.whisper_model,
                           openai_api_key=cfg.openai_api_key)
    text = t.transcribe(audio)
    typer.echo(f"Transcribed: {text}")
    return text
```

- [ ] **Step 3: Verify entry points still work**

```bash
creator --help
lc skill --help
lc prompt --help
```
Expected: Typer help for all three.

- [ ] **Step 4: Run all Python tests**

```bash
pytest tests/ -q
```
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add creator/cli.py
git commit -m "feat(sp3): rewrite CLI with skill/prompt sub-apps and --voice flag"
```

---

### Task 9: FastAPI routes for skills + wire into `main.py`

**Files:**
- Create: `tauri-app/lc_server/routes/skills.py`
- Modify: `tauri-app/lc_server/main.py`
- Create: `tauri-app/tests/server/test_skills.py`

**Interfaces:**
- Consumes: `SkillSpec` (Task 4), `save_skill_spec`, `load_skill_spec`, `list_skills`, `delete_skill`, `publish_skill`, `skill_dir` (Task 4), `run_skill` (Task 5), `GenerationEvent`, `Variant` from `creator.gepa.engine`
- Produces: REST endpoints:
  - `GET /api/skills` → `list[{name, category, last_modified}]`
  - `POST /api/skills` body: SkillSpec JSON → `{name}`
  - `GET /api/skills/{name}` → SkillSpec JSON
  - `DELETE /api/skills/{name}` → `{ok: true}`
  - `POST /api/skills/{name}/run` → SSE stream of GenerationEvents
  - `GET /api/skills/{name}/output` → `{content: str}` (SKILL.md)
  - `POST /api/skills/{name}/publish` → `{dest: str}`

- [ ] **Step 1: Write the failing tests**

```python
# tauri-app/tests/server/test_skills.py
import json, yaml, pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from creator.gepa.engine import GenerationEvent, Variant
from creator.skills.spec import SkillSpec
from creator.spec import GeneratorSpec, JudgeSpec


def _make_skill(tmp_path, name="myskill"):
    d = tmp_path / ".creator" / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    spec = SkillSpec(
        name=name, description_goal="Do code review", category="code-review",
        generator=GeneratorSpec(cli="claude"), judge=JudgeSpec(cli="claude"),
    )
    (d / "spec.yaml").write_text(yaml.dump(spec.model_dump()))
    return d


def _fake_variant():
    return Variant(prompt="p", output="# myskill\nDo reviews.", score=0.91, reason="great", generation=1)


def _fake_run_skill(spec, skill_dir, on_event=None):
    v = _fake_variant()
    ev = GenerationEvent(generation=1, variants=[v], best_score=0.91)
    done = GenerationEvent(generation=1, variants=[v], best_score=0.91, event_type="done")
    if on_event:
        on_event(ev)
        on_event(done)
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(v.output)
    return v


def test_list_skills(client, tmp_path):
    _make_skill(tmp_path, "alpha")
    _make_skill(tmp_path, "beta")
    r = client.get("/api/skills")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()]
    assert "alpha" in names and "beta" in names


def test_create_skill(client, tmp_path):
    payload = {
        "name": "newskill", "description_goal": "Do stuff", "category": "custom",
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    r = client.post("/api/skills", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "newskill"
    assert (tmp_path / ".creator" / "skills" / "newskill" / "spec.yaml").exists()


def test_get_skill(client, tmp_path):
    _make_skill(tmp_path, "getme")
    r = client.get("/api/skills/getme")
    assert r.status_code == 200
    assert r.json()["name"] == "getme"


def test_delete_skill(client, tmp_path):
    _make_skill(tmp_path, "deleteme")
    r = client.delete("/api/skills/deleteme")
    assert r.status_code == 200
    assert not (tmp_path / ".creator" / "skills" / "deleteme").exists()


def test_run_skill_streams_sse(client, tmp_path):
    _make_skill(tmp_path)
    with patch("lc_server.routes.skills.run_skill", _fake_run_skill):
        r = client.post("/api/skills/myskill/run")
    assert "text/event-stream" in r.headers["content-type"]
    assert "data: " in r.text
    assert "generation" in r.text


def test_get_skill_output(client, tmp_path):
    d = _make_skill(tmp_path)
    (d / "SKILL.md").write_text("# myskill\nDo reviews.")
    r = client.get("/api/skills/myskill/output")
    assert r.status_code == 200
    assert r.json()["content"].startswith("# myskill")


def test_publish_skill(client, tmp_path):
    d = _make_skill(tmp_path)
    (d / "SKILL.md").write_text("# myskill\n")
    claude_skills = tmp_path / ".claude" / "skills"
    with patch("creator.skills.registry._claude_skills_base", return_value=claude_skills):
        r = client.post("/api/skills/myskill/publish")
    assert r.status_code == 200
    assert "dest" in r.json()
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app && pytest tests/server/test_skills.py -v
```
Expected: FAIL.

- [ ] **Step 3: Implement `tauri-app/lc_server/routes/skills.py`**

```python
import asyncio, json, threading
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from creator.skills.spec import SkillSpec
from creator.skills.registry import (
    skill_dir, save_skill_spec, load_skill_spec, list_skills, delete_skill, publish_skill,
)
from creator.skills.runner import run_skill

router = APIRouter(prefix="/api/skills")


@router.get("")
def get_skills():
    return list_skills()


@router.post("")
def create_skill(spec: SkillSpec):
    save_skill_spec(spec)
    return {"name": spec.name}


@router.get("/{name}")
def get_skill(name: str):
    d = skill_dir(name)
    if not (d / "spec.yaml").exists():
        raise HTTPException(status_code=404, detail="Skill not found")
    return load_skill_spec(name).model_dump()


@router.delete("/{name}")
def remove_skill(name: str):
    d = skill_dir(name)
    if not d.exists():
        raise HTTPException(status_code=404, detail="Skill not found")
    delete_skill(name)
    return {"ok": True}


@router.post("/{name}/run")
def run_skill_sse(name: str):
    d = skill_dir(name)
    if not (d / "spec.yaml").exists():
        raise HTTPException(status_code=404, detail="Skill not found")
    spec = load_skill_spec(name)

    queue: asyncio.Queue = asyncio.Queue()

    def worker():
        def on_event(ev):
            queue.put_nowait(json.dumps(ev.model_dump()))
        run_skill(spec, d, on_event=on_event)
        queue.put_nowait(None)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    def event_stream():
        loop = asyncio.new_event_loop()
        while True:
            item = loop.run_until_complete(queue.get())
            if item is None:
                break
            yield f"data: {item}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{name}/output")
def get_skill_output(name: str):
    output = skill_dir(name) / "SKILL.md"
    if not output.exists():
        raise HTTPException(status_code=404, detail="No output yet")
    return {"content": output.read_text()}


@router.post("/{name}/publish")
def publish_skill_endpoint(name: str):
    d = skill_dir(name)
    if not (d / "SKILL.md").exists():
        raise HTTPException(status_code=400, detail="Run the skill first to generate SKILL.md")
    dest = publish_skill(name)
    return {"dest": str(dest)}
```

- [ ] **Step 4: Update `tauri-app/lc_server/main.py`** — add skills router

```python
# In create_app(), add after existing router includes:
from lc_server.routes import skills as skills_routes
app.include_router(skills_routes.router)
```

- [ ] **Step 5: Run tests to confirm passing**

```bash
cd tauri-app && pytest tests/server/test_skills.py -v
```
Expected: PASS (7 tests).

- [ ] **Step 6: Commit**

```bash
git add tauri-app/lc_server/routes/skills.py tauri-app/lc_server/main.py tauri-app/tests/server/test_skills.py
git commit -m "feat(sp3): /api/skills CRUD + SSE run + publish endpoints"
```

---

### Task 10: FastAPI routes for prompts, config, and transcribe

**Files:**
- Create: `tauri-app/lc_server/routes/prompts.py`
- Create: `tauri-app/lc_server/routes/config.py`
- Create: `tauri-app/lc_server/routes/transcribe.py`
- Modify: `tauri-app/lc_server/main.py`
- Create: `tauri-app/tests/server/test_prompts.py`
- Create: `tauri-app/tests/server/test_config_route.py`
- Create: `tauri-app/tests/server/test_transcribe.py`

**Interfaces:**
- Consumes: `PromptSpec` (Task 6), prompt registry (Task 6), `run_prompt`, `fill_prompt` (Task 7), `CreatorConfig`, `load_config`, `save_config` (Task 2), `WhisperTranscriber` (Task 3)
- Produces:
  - `GET /api/prompts`, `POST /api/prompts`, `GET /api/prompts/{name}`, `DELETE /api/prompts/{name}`
  - `POST /api/prompts/{name}/run` → SSE
  - `GET /api/prompts/{name}/output` → `{content: str}`
  - `POST /api/prompts/{name}/use` body: `{variables: {key: val}}` → `{resolved: str}`
  - `GET /api/config` → CreatorConfig JSON
  - `PUT /api/config` body: CreatorConfig JSON → CreatorConfig JSON
  - `POST /api/transcribe` multipart `audio` file → `{text: str}`

- [ ] **Step 1: Write the failing tests**

```python
# tauri-app/tests/server/test_prompts.py
import json, yaml, pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from creator.gepa.engine import GenerationEvent, Variant
from creator.prompts.spec import PromptSpec
from creator.spec import GeneratorSpec, JudgeSpec


def _make_prompt(tmp_path, name="myprompt"):
    d = tmp_path / ".creator" / "prompts" / name
    d.mkdir(parents=True, exist_ok=True)
    spec = PromptSpec(
        name=name, description_goal="Generate commit messages", variables=["diff"],
        generator=GeneratorSpec(cli="claude"), judge=JudgeSpec(cli="claude"),
    )
    (d / "spec.yaml").write_text(yaml.dump(spec.model_dump()))
    return d


def _fake_run_prompt(spec, prompt_dir, on_event=None):
    v = Variant(prompt="p", output="Write for {{diff}}.", score=0.92, reason="good", generation=1)
    ev = GenerationEvent(generation=1, variants=[v], best_score=0.92)
    done = GenerationEvent(generation=1, variants=[v], best_score=0.92, event_type="done")
    if on_event:
        on_event(ev); on_event(done)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / f"{spec.name}.md").write_text(v.output)
    return v


def test_list_prompts(client, tmp_path):
    _make_prompt(tmp_path, "a")
    _make_prompt(tmp_path, "b")
    r = client.get("/api/prompts")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert "a" in names and "b" in names


def test_create_prompt(client, tmp_path):
    payload = {
        "name": "newprompt", "description_goal": "Make commits", "variables": ["diff"],
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    r = client.post("/api/prompts", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "newprompt"


def test_delete_prompt(client, tmp_path):
    _make_prompt(tmp_path, "del")
    r = client.delete("/api/prompts/del")
    assert r.status_code == 200
    assert not (tmp_path / ".creator" / "prompts" / "del").exists()


def test_run_prompt_streams_sse(client, tmp_path):
    _make_prompt(tmp_path)
    with patch("lc_server.routes.prompts.run_prompt", _fake_run_prompt):
        r = client.post("/api/prompts/myprompt/run")
    assert "text/event-stream" in r.headers["content-type"]


def test_use_prompt(client, tmp_path):
    d = _make_prompt(tmp_path)
    (d / "myprompt.md").write_text("Write for {{diff}}.")
    r = client.post("/api/prompts/myprompt/use", json={"variables": {"diff": "added login"}})
    assert r.status_code == 200
    assert r.json()["resolved"] == "Write for added login."
```

```python
# tauri-app/tests/server/test_config_route.py
def test_get_config(client):
    r = client.get("/api/config")
    assert r.status_code == 200
    assert "whisper_backend" in r.json()


def test_put_config(client):
    r = client.put("/api/config", json={"whisper_backend": "openai", "whisper_model": "whisper-1", "openai_api_key": ""})
    assert r.status_code == 200
    assert r.json()["whisper_backend"] == "openai"
```

```python
# tauri-app/tests/server/test_transcribe.py
from unittest.mock import patch


def test_transcribe_returns_text(client):
    audio_bytes = b"RIFF....fake wav"
    with patch("lc_server.routes.transcribe.WhisperTranscriber") as MockT:
        MockT.return_value.transcribe.return_value = "hello world"
        r = client.post(
            "/api/transcribe",
            files={"audio": ("audio.wav", audio_bytes, "audio/wav")},
        )
    assert r.status_code == 200
    assert r.json()["text"] == "hello world"
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app && pytest tests/server/test_prompts.py tests/server/test_config_route.py tests/server/test_transcribe.py -v
```
Expected: FAIL.

- [ ] **Step 3: Implement `tauri-app/lc_server/routes/prompts.py`**

```python
import asyncio, json, threading
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from creator.prompts.spec import PromptSpec
from creator.prompts.registry import (
    prompt_dir, save_prompt_spec, load_prompt_spec, list_prompts, delete_prompt,
)
from creator.prompts.runner import run_prompt

router = APIRouter(prefix="/api/prompts")


@router.get("")
def get_prompts():
    return list_prompts()


@router.post("")
def create_prompt(spec: PromptSpec):
    save_prompt_spec(spec)
    return {"name": spec.name}


@router.get("/{name}")
def get_prompt(name: str):
    d = prompt_dir(name)
    if not (d / "spec.yaml").exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    return load_prompt_spec(name).model_dump()


@router.delete("/{name}")
def remove_prompt(name: str):
    d = prompt_dir(name)
    if not d.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    delete_prompt(name)
    return {"ok": True}


@router.post("/{name}/run")
def run_prompt_sse(name: str):
    d = prompt_dir(name)
    if not (d / "spec.yaml").exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    spec = load_prompt_spec(name)
    queue: asyncio.Queue = asyncio.Queue()

    def worker():
        def on_event(ev):
            queue.put_nowait(json.dumps(ev.model_dump()))
        run_prompt(spec, d, on_event=on_event)
        queue.put_nowait(None)

    threading.Thread(target=worker, daemon=True).start()

    def event_stream():
        loop = asyncio.new_event_loop()
        while True:
            item = loop.run_until_complete(queue.get())
            if item is None:
                break
            yield f"data: {item}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{name}/output")
def get_prompt_output(name: str):
    output = prompt_dir(name) / f"{name}.md"
    if not output.exists():
        raise HTTPException(status_code=404, detail="No output yet")
    return {"content": output.read_text()}


@router.post("/{name}/use")
def use_prompt(name: str, body: dict):
    output = prompt_dir(name) / f"{name}.md"
    if not output.exists():
        raise HTTPException(status_code=404, detail="No output yet — run the prompt first")
    template = output.read_text()
    if template.startswith("---"):
        end = template.find("---", 3)
        template = template[end + 3:].lstrip("\n")
    variables = body.get("variables", {})
    for key, val in variables.items():
        template = template.replace(f"{{{{{key}}}}}", val)
    return {"resolved": template}
```

- [ ] **Step 4: Implement `tauri-app/lc_server/routes/config.py`**

```python
from fastapi import APIRouter
from creator.config import CreatorConfig, load_config, save_config

router = APIRouter(prefix="/api/config")


@router.get("")
def get_config():
    return load_config().model_dump()


@router.put("")
def put_config(cfg: CreatorConfig):
    save_config(cfg)
    return cfg.model_dump()
```

- [ ] **Step 5: Implement `tauri-app/lc_server/routes/transcribe.py`**

```python
from fastapi import APIRouter, UploadFile, File
from creator.audio.whisper import WhisperTranscriber
from creator.config import load_config

router = APIRouter(prefix="/api/transcribe")


@router.post("")
async def transcribe(audio: UploadFile = File(...)):
    cfg = load_config()
    audio_bytes = await audio.read()
    t = WhisperTranscriber(
        backend=cfg.whisper_backend,
        model=cfg.whisper_model,
        openai_api_key=cfg.openai_api_key,
    )
    text = t.transcribe(audio_bytes)
    return {"text": text}
```

- [ ] **Step 6: Update `tauri-app/lc_server/main.py`** — add three new routers

```python
from lc_server.routes import prompts as prompts_routes
from lc_server.routes import config as config_routes
from lc_server.routes import transcribe as transcribe_routes

# In create_app():
app.include_router(prompts_routes.router)
app.include_router(config_routes.router)
app.include_router(transcribe_routes.router)
```

- [ ] **Step 7: Run tests to confirm passing**

```bash
cd tauri-app && pytest tests/server/test_prompts.py tests/server/test_config_route.py tests/server/test_transcribe.py -v
```
Expected: PASS (all tests).

- [ ] **Step 8: Confirm all server tests still pass**

```bash
cd tauri-app && pytest tests/ -q
```
Expected: all green.

- [ ] **Step 9: Commit**

```bash
git add tauri-app/lc_server/routes/prompts.py tauri-app/lc_server/routes/config.py tauri-app/lc_server/routes/transcribe.py tauri-app/lc_server/main.py tauri-app/tests/server/test_prompts.py tauri-app/tests/server/test_config_route.py tauri-app/tests/server/test_transcribe.py
git commit -m "feat(sp3): /api/prompts, /api/config, /api/transcribe endpoints"
```

---

### Task 11: TypeScript types + `useSkill`, `usePrompt`, `useTranscribe` hooks

**Files:**
- Modify: `tauri-app/web/src/types.ts`
- Create: `tauri-app/web/src/hooks/useSkill.ts`
- Create: `tauri-app/web/src/hooks/usePrompt.ts`
- Create: `tauri-app/web/src/hooks/useTranscribe.ts`
- Create: `tauri-app/web/src/hooks/__tests__/useSkill.test.ts`
- Create: `tauri-app/web/src/hooks/__tests__/useTranscribe.test.ts`

**Interfaces:**
- Consumes: existing `GenerationEvent`, `Variant` types; `useLoop` hook pattern from `tauri-app/web/src/hooks/useLoop.ts`
- Produces:
  - `SkillSpec`, `SkillSummary`, `PromptSpec`, `PromptSummary`, `AppConfig` TypeScript interfaces
  - `useSkill()` → `{ events, bestVariant, isRunning, error, run(name), stop }`
  - `usePrompt()` → same shape as `useSkill` but `run(name)` hits `/api/prompts/`
  - `useTranscribe()` → `{ isRecording, startRecording, stopAndTranscribe: () => Promise<string> }`

- [ ] **Step 1: Write the failing tests**

```typescript
// tauri-app/web/src/hooks/__tests__/useSkill.test.ts
import { renderHook, act } from "@testing-library/react";
import { useSkill } from "../useSkill";

(window as any).__LC_PORT__ = 5001;

function makeSSEBody(events: object[]): ReadableStream {
  const chunks = events.map(e => new TextEncoder().encode(`data: ${JSON.stringify(e)}\n\n`));
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) controller.enqueue(chunks[i++]);
      else controller.close();
    },
  });
}

test("run sets isRunning then clears on done", async () => {
  const doneEvent = { generation: 1, variants: [{ prompt:"p", output:"o", score:0.9, reason:"r", generation:1 }], best_score: 0.9, event_type: "done" };
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: makeSSEBody([doneEvent]),
  } as any);

  const { result } = renderHook(() => useSkill());
  await act(async () => { await result.current.run("myskill"); });

  expect(result.current.isRunning).toBe(false);
  expect(result.current.bestVariant?.score).toBe(0.9);
});

test("stop aborts the run", () => {
  const { result } = renderHook(() => useSkill());
  act(() => result.current.stop());
  expect(result.current.isRunning).toBe(false);
});
```

```typescript
// tauri-app/web/src/hooks/__tests__/useTranscribe.test.ts
import { renderHook, act } from "@testing-library/react";
import { useTranscribe } from "../useTranscribe";

(window as any).__LC_PORT__ = 5001;

test("stopAndTranscribe posts audio and returns text", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ text: "hello world" }),
  } as any);

  const mockMediaRecorder = {
    start: vi.fn(),
    stop: vi.fn(),
    ondataavailable: null as any,
    onstop: null as any,
  };
  (global as any).MediaRecorder = vi.fn(() => mockMediaRecorder);
  (global as any).navigator = {
    mediaDevices: { getUserMedia: vi.fn().mockResolvedValue({}) },
  };

  const { result } = renderHook(() => useTranscribe());

  await act(async () => { result.current.startRecording(); });
  mockMediaRecorder.ondataavailable?.({ data: new Blob(["audio"]) } as any);
  mockMediaRecorder.onstop?.();

  const textPromise = result.current.stopAndTranscribe();
  mockMediaRecorder.onstop?.();
  const text = await textPromise;
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/transcribe"), expect.any(Object));
});
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/hooks/__tests__/useSkill.test.ts src/hooks/__tests__/useTranscribe.test.ts
```
Expected: FAIL.

- [ ] **Step 3: Add SP3 types to `tauri-app/web/src/types.ts`**

Append to the existing types.ts:

```typescript
export interface SkillSummary {
  name: string;
  category: string;
  last_modified: number;
}

export interface SkillSpec {
  name: string;
  description_goal: string;
  category: string;
  target_platforms: string[];
  generator: { cli: string; model: string };
  judge: { cli: string; rubric: string; model: string };
  gepa: { population_size: number; max_generations: number; fitness_threshold: number };
}

export interface PromptSummary {
  name: string;
  description_goal: string;
  last_modified: number;
}

export interface PromptSpec {
  name: string;
  description_goal: string;
  variables: string[];
  generator: { cli: string; model: string };
  judge: { cli: string; rubric: string; model: string };
  gepa: { population_size: number; max_generations: number; fitness_threshold: number };
}

export interface AppConfig {
  whisper_backend: string;
  whisper_model: string;
  openai_api_key: string;
}
```

- [ ] **Step 4: Implement `tauri-app/web/src/hooks/useSkill.ts`**

```typescript
import { useState, useCallback, useRef } from "react";
import type { GenerationEvent, Variant } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function useSkill() {
  const [events, setEvents] = useState<GenerationEvent[]>([]);
  const [bestVariant, setBestVariant] = useState<Variant | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(async (name: string) => {
    setIsRunning(true);
    setEvents([]);
    setBestVariant(null);
    setError(null);
    abortRef.current = new AbortController();
    try {
      const res = await fetch(`http://localhost:${port()}/api/skills/${name}/run`, {
        method: "POST",
        signal: abortRef.current.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let sseBuffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        sseBuffer += decoder.decode(value, { stream: true });
        const parts = sseBuffer.split("\n\n");
        sseBuffer = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.replace(/^data: /, "").trim();
          if (!line) continue;
          const ev: GenerationEvent = JSON.parse(line);
          setEvents(prev => [...prev, ev]);
          if (ev.event_type === "done" && ev.variants.length > 0) {
            setBestVariant(ev.variants[0]);
          }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsRunning(false);
  }, []);

  return { events, bestVariant, isRunning, error, run, stop };
}
```

- [ ] **Step 5: Implement `tauri-app/web/src/hooks/usePrompt.ts`**

```typescript
import { useState, useCallback, useRef } from "react";
import type { GenerationEvent, Variant } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function usePrompt() {
  const [events, setEvents] = useState<GenerationEvent[]>([]);
  const [bestVariant, setBestVariant] = useState<Variant | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(async (name: string) => {
    setIsRunning(true);
    setEvents([]);
    setBestVariant(null);
    setError(null);
    abortRef.current = new AbortController();
    try {
      const res = await fetch(`http://localhost:${port()}/api/prompts/${name}/run`, {
        method: "POST",
        signal: abortRef.current.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let sseBuffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        sseBuffer += decoder.decode(value, { stream: true });
        const parts = sseBuffer.split("\n\n");
        sseBuffer = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.replace(/^data: /, "").trim();
          if (!line) continue;
          const ev: GenerationEvent = JSON.parse(line);
          setEvents(prev => [...prev, ev]);
          if (ev.event_type === "done" && ev.variants.length > 0) {
            setBestVariant(ev.variants[0]);
          }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsRunning(false);
  }, []);

  return { events, bestVariant, isRunning, error, run, stop };
}
```

- [ ] **Step 6: Implement `tauri-app/web/src/hooks/useTranscribe.ts`**

```typescript
import { useState, useRef, useCallback } from "react";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function useTranscribe() {
  const [isRecording, setIsRecording] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
    recorder.start();
    recorderRef.current = recorder;
    setIsRecording(true);
  }, []);

  const stopAndTranscribe = useCallback((): Promise<string> => {
    return new Promise((resolve, reject) => {
      const recorder = recorderRef.current;
      if (!recorder) { reject(new Error("Not recording")); return; }
      recorder.onstop = async () => {
        setIsRecording(false);
        const blob = new Blob(chunksRef.current, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("audio", blob, "audio.wav");
        try {
          const res = await fetch(`http://localhost:${port()}/api/transcribe`, {
            method: "POST",
            body: formData,
          });
          const data = await res.json();
          resolve(data.text as string);
        } catch (e) {
          reject(e);
        }
      };
      recorder.stop();
    });
  }, []);

  return { isRecording, startRecording, stopAndTranscribe };
}
```

- [ ] **Step 7: Run hook tests to confirm passing**

```bash
cd tauri-app/web && npx vitest run src/hooks/__tests__/useSkill.test.ts src/hooks/__tests__/useTranscribe.test.ts
```
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tauri-app/web/src/types.ts tauri-app/web/src/hooks/useSkill.ts tauri-app/web/src/hooks/usePrompt.ts tauri-app/web/src/hooks/useTranscribe.ts tauri-app/web/src/hooks/__tests__/useSkill.test.ts tauri-app/web/src/hooks/__tests__/useTranscribe.test.ts
git commit -m "feat(sp3): useSkill, usePrompt, useTranscribe hooks + SP3 TypeScript types"
```

---

### Task 12: `SkillList.tsx` + `SkillBuilder.tsx`

**Files:**
- Create: `tauri-app/web/src/pages/SkillList.tsx`
- Create: `tauri-app/web/src/pages/SkillBuilder.tsx`
- Create: `tauri-app/web/src/pages/__tests__/SkillList.test.tsx`
- Create: `tauri-app/web/src/pages/__tests__/SkillBuilder.test.tsx`

**Interfaces:**
- Consumes: `SkillSummary`, `SkillSpec` (Task 11), `/api/skills` endpoints (Task 9)
- Produces: `SkillList` component (lists skills, links to `/skills/new`, `/skills/:name/run`, `/skills/:name/edit`); `SkillBuilder` component (create/edit form with name, description_goal, category select, generator.cli select)

- [ ] **Step 1: Write the failing tests**

```tsx
// tauri-app/web/src/pages/__tests__/SkillList.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { SkillList } from "../SkillList";

(window as any).__LC_PORT__ = 5001;

test("shows empty state when no skills", async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: async () => [] } as any);
  render(<MemoryRouter><SkillList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText(/No skills yet/)).toBeInTheDocument());
});

test("renders skill rows", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [{ name: "my-reviewer", category: "code-review", last_modified: 0 }],
  } as any);
  render(<MemoryRouter><SkillList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText("my-reviewer")).toBeInTheDocument());
  expect(screen.getByText("code-review")).toBeInTheDocument();
});
```

```tsx
// tauri-app/web/src/pages/__tests__/SkillBuilder.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { SkillBuilder } from "../SkillBuilder";

(window as any).__LC_PORT__ = 5001;

test("renders all form fields", () => {
  render(<MemoryRouter><SkillBuilder /></MemoryRouter>);
  expect(screen.getByLabelText(/Skill Name/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Description Goal/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Category/i)).toBeInTheDocument();
});

test("submits new skill and navigates", async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: async () => ({ name: "newskill" }) } as any);
  render(<MemoryRouter><SkillBuilder /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/Skill Name/i), { target: { value: "newskill" } });
  fireEvent.change(screen.getByLabelText(/Description Goal/i), { target: { value: "Do reviews" } });
  fireEvent.click(screen.getByRole("button", { name: /Save/i }));
  await waitFor(() => expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/skills"),
    expect.objectContaining({ method: "POST" }),
  ));
});
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/SkillList.test.tsx src/pages/__tests__/SkillBuilder.test.tsx
```
Expected: FAIL.

- [ ] **Step 3: Implement `SkillList.tsx`**

```tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { SkillSummary } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function SkillList() {
  const [skills, setSkills] = useState<SkillSummary[]>([]);

  useEffect(() => {
    fetch(`http://localhost:${port()}/api/skills`)
      .then(r => r.json())
      .then(setSkills);
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>Skills</h2>
        <Link to="/skills/new" style={{ color: "#01C7B1", textDecoration: "none", fontWeight: 600 }}>
          + New Skill
        </Link>
      </div>
      {skills.length === 0 ? (
        <p style={{ color: "#8A8A8A" }}>No skills yet — create one to get started.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ color: "#8A8A8A", fontSize: 12, textAlign: "left" }}>
              <th style={{ padding: "8px 12px" }}>Name</th>
              <th style={{ padding: "8px 12px" }}>Category</th>
              <th style={{ padding: "8px 12px" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {skills.map(s => (
              <tr key={s.name} style={{ borderTop: "1px solid #383838" }}>
                <td style={{ padding: "12px", color: "#F0F0F0" }}>{s.name}</td>
                <td style={{ padding: "12px", color: "#8A8A8A" }}>{s.category}</td>
                <td style={{ padding: "12px", display: "flex", gap: 8 }}>
                  <Link to={`/skills/${s.name}/run`} style={{ color: "#01C7B1" }}>Run</Link>
                  <Link to={`/skills/${s.name}/edit`} style={{ color: "#9B6DFF" }}>Edit</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Implement `SkillBuilder.tsx`**

```tsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const port = () => (window as any).__LC_PORT__ ?? 5001;
const CATEGORIES = ["code-review", "testing", "documentation", "devops", "data-analysis", "custom"];
const CLI_OPTIONS = ["claude", "ollama", "devin"];

export function SkillBuilder() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "", description_goal: "", category: "custom",
    generator_cli: "claude", judge_cli: "claude",
  });

  useEffect(() => {
    if (name) {
      fetch(`http://localhost:${port()}/api/skills/${name}`)
        .then(r => r.json())
        .then(spec => setForm({
          name: spec.name, description_goal: spec.description_goal, category: spec.category,
          generator_cli: spec.generator.cli, judge_cli: spec.judge.cli,
        }));
    }
  }, [name]);

  const save = async () => {
    const payload = {
      name: form.name, description_goal: form.description_goal, category: form.category,
      generator: { cli: form.generator_cli, model: "" },
      judge: { cli: form.judge_cli, rubric: "", model: "" },
    };
    await fetch(`http://localhost:${port()}/api/skills`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    navigate("/skills");
  };

  const field = (label: string, id: string, value: string, onChange: (v: string) => void, multiline = false) => (
    <div style={{ marginBottom: 16 }}>
      <label htmlFor={id} style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
        {label}
      </label>
      {multiline ? (
        <textarea id={id} value={value} onChange={e => onChange(e.target.value)}
          rows={4}
          style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
            color: "#F0F0F0", padding: "8px 12px", fontSize: 14, resize: "vertical" }} />
      ) : (
        <input id={id} value={value} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
            color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }} />
      )}
    </div>
  );

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <h2 style={{ color: "#F0F0F0", marginBottom: 24 }}>{name ? "Edit Skill" : "New Skill"}</h2>
      {field("Skill Name", "skill-name", form.name, v => setForm(f => ({ ...f, name: v })))}
      {field("Description Goal", "description-goal", form.description_goal,
        v => setForm(f => ({ ...f, description_goal: v })), true)}
      <div style={{ marginBottom: 16 }}>
        <label htmlFor="category" style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
          Category
        </label>
        <select id="category" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
          style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
            color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }}>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <button onClick={save}
        style={{ background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6,
          padding: "10px 24px", fontWeight: 700, cursor: "pointer", fontSize: 15 }}>
        Save Skill
      </button>
    </div>
  );
}
```

- [ ] **Step 5: Run tests to confirm passing**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/SkillList.test.tsx src/pages/__tests__/SkillBuilder.test.tsx
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tauri-app/web/src/pages/SkillList.tsx tauri-app/web/src/pages/SkillBuilder.tsx tauri-app/web/src/pages/__tests__/SkillList.test.tsx tauri-app/web/src/pages/__tests__/SkillBuilder.test.tsx
git commit -m "feat(sp3): SkillList and SkillBuilder pages"
```

---

### Task 13: `SkillDashboard.tsx`

**Files:**
- Create: `tauri-app/web/src/pages/SkillDashboard.tsx`
- Create: `tauri-app/web/src/pages/__tests__/SkillDashboard.test.tsx`

**Interfaces:**
- Consumes: `useSkill` (Task 11), `EvolutionViewer` and `ResultsPanel` from existing SP2 components
- Produces: `SkillDashboard` component — shows skill name, Run/Stop button, EvolutionViewer stream, ResultsPanel with SKILL.md output

- [ ] **Step 1: Write the failing test**

```tsx
// tauri-app/web/src/pages/__tests__/SkillDashboard.test.tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SkillDashboard } from "../SkillDashboard";

(window as any).__LC_PORT__ = 5001;

test("renders skill name and run button", () => {
  render(
    <MemoryRouter initialEntries={["/skills/myskill/run"]}>
      <Routes>
        <Route path="/skills/:name/run" element={<SkillDashboard />} />
      </Routes>
    </MemoryRouter>
  );
  expect(screen.getByText(/myskill/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Run/i })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/SkillDashboard.test.tsx
```
Expected: FAIL.

- [ ] **Step 3: Implement `SkillDashboard.tsx`**

```tsx
import { useParams, Link } from "react-router-dom";
import { useSkill } from "../hooks/useSkill";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function SkillDashboard() {
  const { name } = useParams<{ name: string }>();
  const { events, bestVariant, isRunning, error, run, stop } = useSkill();

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <Link to="/skills" style={{ color: "#8A8A8A", textDecoration: "none" }}>← Skills</Link>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>{name}</h2>
        {isRunning ? (
          <button onClick={stop}
            style={{ background: "#9B6DFF", color: "#1C1C1C", border: "none", borderRadius: 6,
              padding: "8px 20px", fontWeight: 700, cursor: "pointer" }}>
            Stop
          </button>
        ) : (
          <button onClick={() => run(name!)}
            style={{ background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6,
              padding: "8px 20px", fontWeight: 700, cursor: "pointer" }}>
            Run
          </button>
        )}
        <Link to={`/skills/${name}/edit`}
          style={{ color: "#9B6DFF", textDecoration: "none", marginLeft: "auto" }}>
          Edit
        </Link>
      </div>
      {error && <p style={{ color: "#ff6b6b" }}>{error}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <EvolutionViewer events={events} />
        <ResultsPanel
          bestVariant={bestVariant}
          outputUrl={`http://localhost:${port()}/api/skills/${name}/output`}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to confirm passing**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/SkillDashboard.test.tsx
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tauri-app/web/src/pages/SkillDashboard.tsx tauri-app/web/src/pages/__tests__/SkillDashboard.test.tsx
git commit -m "feat(sp3): SkillDashboard page with SSE evolution viewer"
```

---

### Task 14: `PromptList.tsx` + `PromptBuilder.tsx`

**Files:**
- Create: `tauri-app/web/src/pages/PromptList.tsx`
- Create: `tauri-app/web/src/pages/PromptBuilder.tsx`
- Create: `tauri-app/web/src/pages/__tests__/PromptList.test.tsx`
- Create: `tauri-app/web/src/pages/__tests__/PromptBuilder.test.tsx`

**Interfaces:**
- Consumes: `PromptSummary`, `PromptSpec` (Task 11), `/api/prompts` endpoints (Task 10)
- Produces: `PromptList` component; `PromptBuilder` component with name, description_goal, variables (comma-separated input), generator/judge CLI selects

- [ ] **Step 1: Write the failing tests**

```tsx
// tauri-app/web/src/pages/__tests__/PromptList.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PromptList } from "../PromptList";

(window as any).__LC_PORT__ = 5001;

test("shows empty state", async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: async () => [] } as any);
  render(<MemoryRouter><PromptList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText(/No prompts yet/)).toBeInTheDocument());
});

test("renders prompt rows", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [{ name: "commit-msg", description_goal: "Generate commit messages", last_modified: 0 }],
  } as any);
  render(<MemoryRouter><PromptList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText("commit-msg")).toBeInTheDocument());
});
```

```tsx
// tauri-app/web/src/pages/__tests__/PromptBuilder.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PromptBuilder } from "../PromptBuilder";

(window as any).__LC_PORT__ = 5001;

test("renders all form fields", () => {
  render(<MemoryRouter><PromptBuilder /></MemoryRouter>);
  expect(screen.getByLabelText(/Prompt Name/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Description Goal/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Variables/i)).toBeInTheDocument();
});

test("submits new prompt", async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: async () => ({ name: "myprompt" }) } as any);
  render(<MemoryRouter><PromptBuilder /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/Prompt Name/i), { target: { value: "myprompt" } });
  fireEvent.change(screen.getByLabelText(/Description Goal/i), { target: { value: "Make commits" } });
  fireEvent.click(screen.getByRole("button", { name: /Save/i }));
  await waitFor(() => expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/prompts"), expect.objectContaining({ method: "POST" }),
  ));
});
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/PromptList.test.tsx src/pages/__tests__/PromptBuilder.test.tsx
```
Expected: FAIL.

- [ ] **Step 3: Implement `PromptList.tsx`**

```tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { PromptSummary } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function PromptList() {
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);

  useEffect(() => {
    fetch(`http://localhost:${port()}/api/prompts`)
      .then(r => r.json())
      .then(setPrompts);
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>Prompts</h2>
        <Link to="/prompts/new" style={{ color: "#01C7B1", textDecoration: "none", fontWeight: 600 }}>
          + New Prompt
        </Link>
      </div>
      {prompts.length === 0 ? (
        <p style={{ color: "#8A8A8A" }}>No prompts yet — create one to get started.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ color: "#8A8A8A", fontSize: 12, textAlign: "left" }}>
              <th style={{ padding: "8px 12px" }}>Name</th>
              <th style={{ padding: "8px 12px" }}>Goal</th>
              <th style={{ padding: "8px 12px" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {prompts.map(p => (
              <tr key={p.name} style={{ borderTop: "1px solid #383838" }}>
                <td style={{ padding: "12px", color: "#F0F0F0" }}>{p.name}</td>
                <td style={{ padding: "12px", color: "#8A8A8A" }}>{p.description_goal.slice(0, 60)}</td>
                <td style={{ padding: "12px", display: "flex", gap: 8 }}>
                  <Link to={`/prompts/${p.name}/run`} style={{ color: "#01C7B1" }}>Run</Link>
                  <Link to={`/prompts/${p.name}/use`} style={{ color: "#9B6DFF" }}>Use</Link>
                  <Link to={`/prompts/${p.name}/edit`} style={{ color: "#8A8A8A" }}>Edit</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Implement `PromptBuilder.tsx`**

```tsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function PromptBuilder() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "", description_goal: "", variables: "",
    generator_cli: "claude", judge_cli: "claude",
  });

  useEffect(() => {
    if (name) {
      fetch(`http://localhost:${port()}/api/prompts/${name}`)
        .then(r => r.json())
        .then(spec => setForm({
          name: spec.name, description_goal: spec.description_goal,
          variables: spec.variables.join(", "),
          generator_cli: spec.generator.cli, judge_cli: spec.judge.cli,
        }));
    }
  }, [name]);

  const save = async () => {
    const payload = {
      name: form.name, description_goal: form.description_goal,
      variables: form.variables.split(",").map((v: string) => v.trim()).filter(Boolean),
      generator: { cli: form.generator_cli, model: "" },
      judge: { cli: form.judge_cli, rubric: "", model: "" },
    };
    await fetch(`http://localhost:${port()}/api/prompts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    navigate("/prompts");
  };

  const inp = (label: string, id: string, value: string, onChange: (v: string) => void, multi = false) => (
    <div style={{ marginBottom: 16 }}>
      <label htmlFor={id} style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
        {label}
      </label>
      {multi ? (
        <textarea id={id} value={value} onChange={e => onChange(e.target.value)} rows={4}
          style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
            color: "#F0F0F0", padding: "8px 12px", fontSize: 14, resize: "vertical" }} />
      ) : (
        <input id={id} value={value} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
            color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }} />
      )}
    </div>
  );

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <h2 style={{ color: "#F0F0F0", marginBottom: 24 }}>{name ? "Edit Prompt" : "New Prompt"}</h2>
      {inp("Prompt Name", "prompt-name", form.name, v => setForm(f => ({ ...f, name: v })))}
      {inp("Description Goal", "description-goal", form.description_goal,
        v => setForm(f => ({ ...f, description_goal: v })), true)}
      {inp("Variables (comma-separated)", "variables", form.variables, v => setForm(f => ({ ...f, variables: v })))}
      <button onClick={save}
        style={{ background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6,
          padding: "10px 24px", fontWeight: 700, cursor: "pointer", fontSize: 15 }}>
        Save Prompt
      </button>
    </div>
  );
}
```

- [ ] **Step 5: Run tests to confirm passing**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/PromptList.test.tsx src/pages/__tests__/PromptBuilder.test.tsx
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tauri-app/web/src/pages/PromptList.tsx tauri-app/web/src/pages/PromptBuilder.tsx tauri-app/web/src/pages/__tests__/PromptList.test.tsx tauri-app/web/src/pages/__tests__/PromptBuilder.test.tsx
git commit -m "feat(sp3): PromptList and PromptBuilder pages"
```

---

### Task 15: `PromptDashboard.tsx` + `PromptUse.tsx`

**Files:**
- Create: `tauri-app/web/src/pages/PromptDashboard.tsx`
- Create: `tauri-app/web/src/pages/PromptUse.tsx`
- Create: `tauri-app/web/src/pages/__tests__/PromptDashboard.test.tsx`
- Create: `tauri-app/web/src/pages/__tests__/PromptUse.test.tsx`

**Interfaces:**
- Consumes: `usePrompt` (Task 11), `/api/prompts/{name}/output` (Task 10), `/api/prompts/{name}/use` (Task 10), `EvolutionViewer`, `ResultsPanel` from SP2
- Produces: `PromptDashboard` (Run/Stop + EvolutionViewer + output panel); `PromptUse` (variable input form → resolved prompt display)

- [ ] **Step 1: Write the failing tests**

```tsx
// tauri-app/web/src/pages/__tests__/PromptDashboard.test.tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PromptDashboard } from "../PromptDashboard";

(window as any).__LC_PORT__ = 5001;

test("renders prompt name and run button", () => {
  render(
    <MemoryRouter initialEntries={["/prompts/commit-msg/run"]}>
      <Routes>
        <Route path="/prompts/:name/run" element={<PromptDashboard />} />
      </Routes>
    </MemoryRouter>
  );
  expect(screen.getByText(/commit-msg/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Run/i })).toBeInTheDocument();
});
```

```tsx
// tauri-app/web/src/pages/__tests__/PromptUse.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PromptUse } from "../PromptUse";

(window as any).__LC_PORT__ = 5001;

test("renders variable inputs from spec", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ name: "commit-msg", variables: ["diff", "context"], description_goal: "", generator: {cli:"claude",model:""}, judge: {cli:"claude",rubric:"",model:""}, gepa: {} }) } as any)
    .mockResolvedValue({ json: async () => ({}) } as any);

  render(
    <MemoryRouter initialEntries={["/prompts/commit-msg/use"]}>
      <Routes>
        <Route path="/prompts/:name/use" element={<PromptUse />} />
      </Routes>
    </MemoryRouter>
  );
  await waitFor(() => expect(screen.getByLabelText(/diff/i)).toBeInTheDocument());
  expect(screen.getByLabelText(/context/i)).toBeInTheDocument();
});

test("submits variables and shows resolved text", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ name: "commit-msg", variables: ["diff"], description_goal: "", generator: {cli:"claude",model:""}, judge: {cli:"claude",rubric:"",model:""}, gepa: {} }) } as any)
    .mockResolvedValueOnce({ json: async () => ({ resolved: "Write commit for added login." }) } as any);

  render(
    <MemoryRouter initialEntries={["/prompts/commit-msg/use"]}>
      <Routes>
        <Route path="/prompts/:name/use" element={<PromptUse />} />
      </Routes>
    </MemoryRouter>
  );
  await waitFor(() => screen.getByLabelText(/diff/i));
  fireEvent.change(screen.getByLabelText(/diff/i), { target: { value: "added login" } });
  fireEvent.click(screen.getByRole("button", { name: /Fill/i }));
  await waitFor(() => expect(screen.getByText(/Write commit for added login/)).toBeInTheDocument());
});
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/PromptDashboard.test.tsx src/pages/__tests__/PromptUse.test.tsx
```
Expected: FAIL.

- [ ] **Step 3: Implement `PromptDashboard.tsx`**

```tsx
import { useParams, Link } from "react-router-dom";
import { usePrompt } from "../hooks/usePrompt";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function PromptDashboard() {
  const { name } = useParams<{ name: string }>();
  const { events, bestVariant, isRunning, error, run, stop } = usePrompt();

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <Link to="/prompts" style={{ color: "#8A8A8A", textDecoration: "none" }}>← Prompts</Link>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>{name}</h2>
        {isRunning ? (
          <button onClick={stop}
            style={{ background: "#9B6DFF", color: "#1C1C1C", border: "none", borderRadius: 6,
              padding: "8px 20px", fontWeight: 700, cursor: "pointer" }}>
            Stop
          </button>
        ) : (
          <button onClick={() => run(name!)}
            style={{ background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6,
              padding: "8px 20px", fontWeight: 700, cursor: "pointer" }}>
            Run
          </button>
        )}
        <Link to={`/prompts/${name}/use`}
          style={{ color: "#9B6DFF", textDecoration: "none", marginLeft: "auto" }}>
          Use →
        </Link>
      </div>
      {error && <p style={{ color: "#ff6b6b" }}>{error}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <EvolutionViewer events={events} />
        <ResultsPanel
          bestVariant={bestVariant}
          outputUrl={`http://localhost:${port()}/api/prompts/${name}/output`}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Implement `PromptUse.tsx`**

```tsx
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { PromptSpec } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function PromptUse() {
  const { name } = useParams<{ name: string }>();
  const [spec, setSpec] = useState<PromptSpec | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [resolved, setResolved] = useState<string | null>(null);

  useEffect(() => {
    fetch(`http://localhost:${port()}/api/prompts/${name}`)
      .then(r => r.json())
      .then((s: PromptSpec) => {
        setSpec(s);
        setValues(Object.fromEntries(s.variables.map(v => [v, ""])));
      });
  }, [name]);

  const fill = async () => {
    const res = await fetch(`http://localhost:${port()}/api/prompts/${name}/use`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ variables: values }),
    });
    const data = await res.json();
    setResolved(data.resolved);
  };

  if (!spec) return <div style={{ padding: 24, color: "#8A8A8A" }}>Loading…</div>;

  return (
    <div style={{ padding: 24, maxWidth: 700 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <Link to="/prompts" style={{ color: "#8A8A8A", textDecoration: "none" }}>← Prompts</Link>
        <h2 style={{ color: "#F0F0F0", margin: 0 }}>Use: {name}</h2>
      </div>
      {spec.variables.map(v => (
        <div key={v} style={{ marginBottom: 16 }}>
          <label htmlFor={v} style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
            {v}
          </label>
          <textarea id={v} value={values[v] ?? ""} rows={3}
            onChange={e => setValues(prev => ({ ...prev, [v]: e.target.value }))}
            style={{ width: "100%", background: "#2E2E2E", border: "1px solid #383838", borderRadius: 6,
              color: "#F0F0F0", padding: "8px 12px", fontSize: 14, resize: "vertical" }} />
        </div>
      ))}
      <button onClick={fill}
        style={{ background: "#9B6DFF", color: "#1C1C1C", border: "none", borderRadius: 6,
          padding: "10px 24px", fontWeight: 700, cursor: "pointer", fontSize: 15, marginBottom: 24 }}>
        Fill Prompt
      </button>
      {resolved && (
        <div style={{ background: "#2E2E2E", border: "1px solid #383838", borderRadius: 8, padding: 16 }}>
          <p style={{ color: "#8A8A8A", margin: "0 0 8px", fontSize: 12 }}>RESOLVED PROMPT</p>
          <pre style={{ color: "#F0F0F0", whiteSpace: "pre-wrap", margin: 0, fontSize: 14 }}>{resolved}</pre>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Run tests to confirm passing**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/PromptDashboard.test.tsx src/pages/__tests__/PromptUse.test.tsx
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tauri-app/web/src/pages/PromptDashboard.tsx tauri-app/web/src/pages/PromptUse.tsx tauri-app/web/src/pages/__tests__/PromptDashboard.test.tsx tauri-app/web/src/pages/__tests__/PromptUse.test.tsx
git commit -m "feat(sp3): PromptDashboard and PromptUse pages"
```

---

### Task 16: `Settings.tsx` + update `Sidebar.tsx` + update `App.tsx`

**Files:**
- Create: `tauri-app/web/src/pages/Settings.tsx`
- Modify: `tauri-app/web/src/components/Sidebar.tsx`
- Modify: `tauri-app/web/src/App.tsx`
- Create: `tauri-app/web/src/pages/__tests__/Settings.test.tsx`

**Interfaces:**
- Consumes: `AppConfig` (Task 11), `/api/config` (Task 10), all 10 new page components (Tasks 12–15)
- Produces: `Settings` page (load/save whisper config); updated Sidebar with 6 nav items; updated App.tsx with 10 new routes

- [ ] **Step 1: Write the failing test**

```tsx
// tauri-app/web/src/pages/__tests__/Settings.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Settings } from "../Settings";

(window as any).__LC_PORT__ = 5001;

test("loads and displays current config", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" }) } as any)
    .mockResolvedValue({ json: async () => ({}) } as any);
  render(<MemoryRouter><Settings /></MemoryRouter>);
  await waitFor(() => expect(screen.getByDisplayValue("local")).toBeInTheDocument());
});

test("saves updated config", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" }) } as any)
    .mockResolvedValueOnce({ json: async () => ({ whisper_backend: "openai", whisper_model: "whisper-1", openai_api_key: "" }) } as any);
  render(<MemoryRouter><Settings /></MemoryRouter>);
  await waitFor(() => screen.getByDisplayValue("local"));
  fireEvent.change(screen.getByLabelText(/Whisper Backend/i), { target: { value: "openai" } });
  fireEvent.click(screen.getByRole("button", { name: /Save/i }));
  await waitFor(() => expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/config"), expect.objectContaining({ method: "PUT" }),
  ));
});
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/Settings.test.tsx
```
Expected: FAIL.

- [ ] **Step 3: Implement `Settings.tsx`**

```tsx
import { useEffect, useState } from "react";
import type { AppConfig } from "../types";

const port = () => (window as any).__LC_PORT__ ?? 5001;

export function Settings() {
  const [config, setConfig] = useState<AppConfig>({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(`http://localhost:${port()}/api/config`)
      .then(r => r.json())
      .then(setConfig);
  }, []);

  const save = async () => {
    await fetch(`http://localhost:${port()}/api/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const field = (label: string, id: string, value: string, onChange: (v: string) => void, options?: string[]) => (
    <div style={{ marginBottom: 20 }}>
      <label htmlFor={id} style={{ display: "block", color: "#8A8A8A", marginBottom: 4, fontSize: 13 }}>
        {label}
      </label>
      {options ? (
        <select id={id} value={value} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", maxWidth: 320, background: "#2E2E2E", border: "1px solid #383838",
            borderRadius: 6, color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }}>
          {options.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input id={id} value={value} onChange={e => onChange(e.target.value)}
          style={{ width: "100%", maxWidth: 320, background: "#2E2E2E", border: "1px solid #383838",
            borderRadius: 6, color: "#F0F0F0", padding: "8px 12px", fontSize: 14 }} />
      )}
    </div>
  );

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ color: "#F0F0F0", marginBottom: 24 }}>Settings</h2>
      {field("Whisper Backend", "whisper-backend", config.whisper_backend,
        v => setConfig(c => ({ ...c, whisper_backend: v })), ["local", "openai"])}
      {field("Whisper Model", "whisper-model", config.whisper_model,
        v => setConfig(c => ({ ...c, whisper_model: v })))}
      {config.whisper_backend === "openai" &&
        field("OpenAI API Key", "openai-key", config.openai_api_key,
          v => setConfig(c => ({ ...c, openai_api_key: v })))}
      <button onClick={save}
        style={{ background: "#01C7B1", color: "#1C1C1C", border: "none", borderRadius: 6,
          padding: "10px 24px", fontWeight: 700, cursor: "pointer", fontSize: 15 }}>
        Save Settings
      </button>
      {saved && <span style={{ color: "#01C7B1", marginLeft: 16, fontSize: 14 }}>Saved!</span>}
    </div>
  );
}
```

- [ ] **Step 4: Update `tauri-app/web/src/components/Sidebar.tsx`**

Replace the existing `NAV` array:

```typescript
const NAV = [
  { to: "/loops", label: "Loops", icon: "⟳" },
  { to: "/new", label: "New Loop", icon: "+" },
  { to: "/skills", label: "Skills", icon: "◈" },
  { to: "/prompts", label: "Prompts", icon: "◉" },
  { to: "/files", label: "Files", icon: "◫" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];
```

- [ ] **Step 5: Update `tauri-app/web/src/App.tsx`** — add 10 new routes

Import all new pages at the top of App.tsx:

```typescript
import { SkillList } from "./pages/SkillList";
import { SkillBuilder } from "./pages/SkillBuilder";
import { SkillDashboard } from "./pages/SkillDashboard";
import { PromptList } from "./pages/PromptList";
import { PromptBuilder } from "./pages/PromptBuilder";
import { PromptDashboard } from "./pages/PromptDashboard";
import { PromptUse } from "./pages/PromptUse";
import { Settings } from "./pages/Settings";
```

Add 10 new routes inside the existing `<Routes>`:

```tsx
<Route path="/skills" element={<SkillList />} />
<Route path="/skills/new" element={<SkillBuilder />} />
<Route path="/skills/:name/edit" element={<SkillBuilder />} />
<Route path="/skills/:name/run" element={<SkillDashboard />} />
<Route path="/prompts" element={<PromptList />} />
<Route path="/prompts/new" element={<PromptBuilder />} />
<Route path="/prompts/:name/edit" element={<PromptBuilder />} />
<Route path="/prompts/:name/run" element={<PromptDashboard />} />
<Route path="/prompts/:name/use" element={<PromptUse />} />
<Route path="/settings" element={<Settings />} />
```

- [ ] **Step 6: Run all web tests to confirm passing**

```bash
cd tauri-app/web && npx vitest run
```
Expected: all tests pass.

- [ ] **Step 7: Run all Python tests to confirm passing**

```bash
cd /path/to/project && pytest tests/ tauri-app/tests/ -q
```
Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add tauri-app/web/src/pages/Settings.tsx tauri-app/web/src/components/Sidebar.tsx tauri-app/web/src/App.tsx tauri-app/web/src/pages/__tests__/Settings.test.tsx
git commit -m "feat(sp3): Settings page, Sidebar 6-item nav, App.tsx 10 new routes — SP3 complete"
```
