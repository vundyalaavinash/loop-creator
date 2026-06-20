# Loop Creator Sub-project 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build loop-creator — a provider-agnostic CLI + TUI tool that runs GEPA-powered evolutionary AI loops for any dev activity, migrating the existing MVP engine and adapters as the foundation.

**Architecture:** Migrate the MVP's `gepa_engine.py`, `scorer.py`, and three CLI adapters into `loop_creator/` as-is (with minimal extensions), then layer a new context system, loop type registry, judge module, Typer CLI, and Textual wizard on top. The GEPA engine is extended to support population-based generation (N variants per generation), context injection, and stagnation/threshold stop conditions.

**Tech Stack:** Python 3.11+, Typer (CLI), Textual (TUI), Pydantic v2 (spec validation), PyYAML (spec loading), httpx (Ollama), tiktoken (token scoring), Rich (output).

## Global Constraints

- Python 3.11+ required (uses `dict | None` union syntax)
- No API keys — all LLM calls go through CLI subprocesses or local Ollama HTTP
- MVP source: `/Users/avinashvundyala/Documents/github/mvp/backend/src/`
- MVP tests: `/Users/avinashvundyala/Documents/github/mvp/backend/tests/`
- Project root: `/Users/avinashvundyala/Documents/github/skills/`
- Python package: `loop_creator/` (inside project root)
- All tests in `tests/` (mirroring `loop_creator/` structure)
- Run tests with: `pytest tests/ -v` from project root
- TDD: write failing test first, then implement

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `loop_creator/__init__.py`
- Create: `loop_creator/adapters/__init__.py`
- Create: `loop_creator/context/__init__.py`
- Create: `loop_creator/gepa/__init__.py`
- Create: `loop_creator/loop_types/__init__.py`
- Create: `loop_creator/wizard/__init__.py`
- Create: `loop_creator/wizard/screens/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/adapters/__init__.py`
- Create: `tests/context/__init__.py`
- Create: `tests/gepa/__init__.py`
- Create: `tests/loop_types/__init__.py`
- Create: `loops/.gitkeep`

**Interfaces:**
- Produces: installable package `loop-creator` with entry point `loop-creator`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "loop-creator"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "textual>=0.61",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "httpx>=0.27",
    "tiktoken>=0.8",
    "rich>=13.0",
]

[project.scripts]
loop-creator = "loop_creator.cli:app"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.hatch.build.targets.wheel]
packages = ["loop_creator"]
```

- [ ] **Step 2: Create all `__init__.py` and placeholder files**

```bash
cd /Users/avinashvundyala/Documents/github/skills
touch loop_creator/__init__.py
touch loop_creator/adapters/__init__.py
touch loop_creator/context/__init__.py
touch loop_creator/gepa/__init__.py
touch loop_creator/loop_types/__init__.py
touch loop_creator/wizard/__init__.py
touch loop_creator/wizard/screens/__init__.py
touch tests/__init__.py
touch tests/adapters/__init__.py
touch tests/context/__init__.py
touch tests/gepa/__init__.py
touch tests/loop_types/__init__.py
mkdir -p loops && touch loops/.gitkeep
```

- [ ] **Step 3: Install in dev mode**

```bash
cd /Users/avinashvundyala/Documents/github/skills
pip install -e ".[dev]" 2>/dev/null || pip install -e .
pip install pytest pytest-asyncio
```

Expected: installs without errors.

- [ ] **Step 4: Verify pytest discovers tests**

```bash
cd /Users/avinashvundyala/Documents/github/skills
pytest tests/ -v --collect-only
```

Expected: `no tests ran` (no tests yet), no import errors.

- [ ] **Step 5: Commit**

```bash
cd /Users/avinashvundyala/Documents/github/skills
git init
git add pyproject.toml loop_creator/ tests/ loops/
git commit -m "feat: scaffold loop-creator project structure"
```

---

### Task 2: Migrate CLI adapters

**Files:**
- Create: `loop_creator/adapters/base.py` (from `mvp/backend/src/llm_adapter.py` + `is_available()`)
- Create: `loop_creator/adapters/claude.py` (from `mvp/backend/src/claude_adapter.py`)
- Create: `loop_creator/adapters/ollama.py` (from `mvp/backend/src/ollama_adapter.py`)
- Create: `loop_creator/adapters/devin.py` (from `mvp/backend/src/devin_adapter.py`)
- Create: `tests/adapters/test_claude.py`
- Create: `tests/adapters/test_ollama.py`
- Create: `tests/adapters/test_devin.py`

**Interfaces:**
- Produces:
  - `LLMAdapter(ABC)` with `call(system, user) -> str`, `call_structured(system, user, schema) -> dict`, `call_structured_with_retry(system, user, schema, retries=2) -> dict`, `is_available() -> bool`
  - `ClaudeAdapter(model="sonnet")` — `is_available()` returns `shutil.which("claude") is not None`
  - `OllamaAdapter(base_url, model)` — `is_available()` tries `GET /api/tags`, returns True if 200
  - `DevinAdapter(api_key, model, base_url, cli_cmd)` — `is_available()` returns True if CLI found or api_key set

- [ ] **Step 1: Write failing tests for is_available()**

Create `tests/adapters/test_claude.py`:

```python
import shutil
from unittest.mock import MagicMock, patch
from loop_creator.adapters.claude import ClaudeAdapter


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    mock = MagicMock()
    mock.stdout = stdout
    mock.stderr = ""
    mock.returncode = returncode
    return mock


def test_call_returns_text():
    with patch("loop_creator.adapters.claude.subprocess.run", return_value=_mock_run("hello")):
        assert ClaudeAdapter().call(system="sys", user="hi") == "hello"


def test_call_structured_parses_json():
    text = 'Some text {"clarity": 80, "specificity": 70, "hallucination_resistance": 60} more'
    with patch("loop_creator.adapters.claude.subprocess.run", return_value=_mock_run(text)):
        result = ClaudeAdapter().call_structured(system="s", user="u", schema={})
    assert result["clarity"] == 80


def test_call_raises_on_nonzero_exit():
    with patch("loop_creator.adapters.claude.subprocess.run", return_value=_mock_run("", returncode=1)):
        import pytest
        with pytest.raises(RuntimeError, match="claude CLI error"):
            ClaudeAdapter().call(system="s", user="u")


def test_is_available_true_when_claude_on_path():
    with patch("loop_creator.adapters.claude.shutil.which", return_value="/usr/bin/claude"):
        assert ClaudeAdapter().is_available() is True


def test_is_available_false_when_not_on_path():
    with patch("loop_creator.adapters.claude.shutil.which", return_value=None):
        assert ClaudeAdapter().is_available() is False
```

Create `tests/adapters/test_ollama.py`:

```python
import httpx
from unittest.mock import MagicMock, patch
from loop_creator.adapters.ollama import OllamaAdapter


def test_call_returns_text():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"message": {"content": "hello"}}
    mock_resp.raise_for_status = MagicMock()
    with patch("loop_creator.adapters.ollama.httpx.post", return_value=mock_resp):
        assert OllamaAdapter().call(system="s", user="u") == "hello"


def test_is_available_true_when_ollama_responds():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("loop_creator.adapters.ollama.httpx.get", return_value=mock_resp):
        assert OllamaAdapter().is_available() is True


def test_is_available_false_on_connection_error():
    with patch("loop_creator.adapters.ollama.httpx.get", side_effect=Exception("refused")):
        assert OllamaAdapter().is_available() is False
```

Create `tests/adapters/test_devin.py`:

```python
from unittest.mock import MagicMock, patch
from loop_creator.adapters.devin import DevinAdapter
import pytest


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    m = MagicMock(); m.stdout = stdout; m.stderr = ""; m.returncode = returncode
    return m


def test_cli_call_returns_text():
    with patch("loop_creator.adapters.devin.shutil.which", return_value="/usr/bin/devin"), \
         patch("loop_creator.adapters.devin.subprocess.run", return_value=_mock_run("ok")):
        assert DevinAdapter().call("s", "u") == "ok"


def test_is_available_true_when_cli_found():
    with patch("loop_creator.adapters.devin.shutil.which", return_value="/usr/bin/devin"):
        assert DevinAdapter().is_available() is True


def test_is_available_true_when_api_key_set():
    with patch("loop_creator.adapters.devin.shutil.which", return_value=None):
        assert DevinAdapter(api_key="tok-123").is_available() is True


def test_is_available_false_when_neither():
    with patch("loop_creator.adapters.devin.shutil.which", return_value=None):
        assert DevinAdapter(api_key="").is_available() is False


def test_raises_when_neither_cli_nor_key():
    with patch("loop_creator.adapters.devin.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="not available"):
            DevinAdapter(api_key="").call("s", "u")
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd /Users/avinashvundyala/Documents/github/skills
pytest tests/adapters/ -v
```

Expected: `ImportError` or `ModuleNotFoundError` — adapters don't exist yet.

- [ ] **Step 3: Create base.py**

```python
# loop_creator/adapters/base.py
import time
from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    @abstractmethod
    def call(self, system: str, user: str) -> str: ...

    @abstractmethod
    def call_structured(self, system: str, user: str, schema: dict) -> dict: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    def call_structured_with_retry(
        self, system: str, user: str, schema: dict, retries: int = 2
    ) -> dict:
        last_error: Exception = RuntimeError("No attempts made")
        for attempt in range(retries + 1):
            try:
                return self.call_structured(system, user, schema)
            except (ValueError, Exception) as e:
                last_error = e
                if attempt < retries:
                    time.sleep(2**attempt)
        raise last_error
```

- [ ] **Step 4: Create claude.py**

```python
# loop_creator/adapters/claude.py
import json
import re
import shutil
import subprocess

from .base import LLMAdapter


class ClaudeAdapter(LLMAdapter):
    def __init__(self, model: str = "sonnet"):
        self.model = model

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    def call(self, system: str, user: str) -> str:
        result = subprocess.run(
            ["claude", "--print", "--system-prompt", system,
             "--model", self.model, "--output-format", "text", user],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")
        return result.stdout.strip()

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        sys_json = system + "\n\nRespond ONLY with valid JSON matching this schema: " + json.dumps(schema)
        response = self.call(sys_json, user)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {response}")
        return json.loads(match.group())
```

- [ ] **Step 5: Create ollama.py**

```python
# loop_creator/adapters/ollama.py
import json
import re

import httpx

from .base import LLMAdapter


class OllamaAdapter(LLMAdapter):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    def call(self, system: str, user: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                  "stream": False},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        sys_json = system + "\n\nRespond ONLY with valid JSON matching this schema: " + json.dumps(schema)
        response = self.call(sys_json, user)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {response}")
        return json.loads(match.group())
```

- [ ] **Step 6: Create devin.py**

```python
# loop_creator/adapters/devin.py
import json
import re
import shutil
import subprocess

import httpx

from .base import LLMAdapter

DEVIN_API_URL = "https://api.cognition.ai/v1"


class DevinAdapter(LLMAdapter):
    def __init__(self, api_key: str = "", model: str = "devin",
                 base_url: str = DEVIN_API_URL, cli_cmd: str = "devin"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.cli_cmd = cli_cmd
        self._cli_available = shutil.which(cli_cmd) is not None

    def is_available(self) -> bool:
        return self._cli_available or bool(self.api_key)

    def call(self, system: str, user: str) -> str:
        if self._cli_available:
            return self._call_cli(system, user)
        if self.api_key:
            return self._call_api(system, user)
        raise RuntimeError(
            "Devin is not available: `devin` CLI not found on PATH and DEVIN_API_KEY is not set."
        )

    def _call_cli(self, system: str, user: str) -> str:
        result = subprocess.run(
            [self.cli_cmd, "run", "--print", f"{system}\n\n{user}"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"devin CLI error: {result.stderr.strip()}")
        return result.stdout.strip()

    def _call_api(self, system: str, user: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        sys_json = system + "\n\nRespond ONLY with valid JSON matching this schema: " + json.dumps(schema)
        response = self.call(sys_json, user)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {response}")
        return json.loads(match.group())
```

- [ ] **Step 7: Run tests — expect all pass**

```bash
cd /Users/avinashvundyala/Documents/github/skills
pytest tests/adapters/ -v
```

Expected: all 13 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add loop_creator/adapters/ tests/adapters/
git commit -m "feat: migrate CLI adapters from MVP with is_available()"
```

---

### Task 3: Migrate scorer

**Files:**
- Create: `loop_creator/gepa/scorer.py` (from `mvp/backend/src/scorer.py`, update imports)
- Create: `tests/gepa/test_scorer.py`

**Interfaces:**
- Produces: `Scorer(adapter: LLMAdapter)` with `score(prompt: str) -> dict` returning keys `token_efficiency, format_control, clarity, specificity, hallucination_resistance, overall` (all int 0-100)

- [ ] **Step 1: Create test file**

```python
# tests/gepa/test_scorer.py
from unittest.mock import MagicMock
from loop_creator.gepa.scorer import Scorer
from loop_creator.adapters.base import LLMAdapter


class MockAdapter(LLMAdapter):
    def call(self, s, u): return '{"clarity":70,"specificity":60,"hallucination_resistance":50}'
    def call_structured(self, s, u, schema): return {"clarity": 70, "specificity": 60, "hallucination_resistance": 50}
    def is_available(self): return True


def test_score_returns_all_dimensions():
    result = Scorer(MockAdapter()).score("Summarize this.")
    assert set(result.keys()) >= {"token_efficiency","format_control","clarity","specificity","hallucination_resistance","overall"}


def test_token_efficiency_penalizes_long_prompts():
    s = Scorer(MockAdapter())
    assert s.score("Summarize.")["token_efficiency"] > s.score("Please provide a very comprehensive and detailed summary of the following long document, making sure to include all key points and nuances. Be thorough.")["token_efficiency"]


def test_format_control_detects_json_instruction():
    s = Scorer(MockAdapter())
    assert s.score("Extract names. Return JSON.")["format_control"] > s.score("Extract names.")["format_control"]


def test_overall_is_average_of_five():
    s = Scorer(MockAdapter())
    r = s.score("Tell me about Python.")
    expected = int((r["token_efficiency"]+r["format_control"]+r["clarity"]+r["specificity"]+r["hallucination_resistance"])/5)
    assert r["overall"] == expected


def test_scores_bounded_0_to_100():
    r = Scorer(MockAdapter()).score("A" * 3000)
    for k, v in r.items():
        assert 0 <= v <= 100, f"{k} out of range: {v}"
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/gepa/test_scorer.py -v
```

- [ ] **Step 3: Create scorer.py**

```python
# loop_creator/gepa/scorer.py
import re

import tiktoken

from loop_creator.adapters.base import LLMAdapter

FORMAT_PATTERNS = [
    r"\bjson\b", r"\bmarkdown\b", r"\bbullets?\b", r"\bbullet list\b",
    r"\bnumbered list\b", r"\bformat:\b", r"\bstructured as\b",
    r"\bin the format\b", r"\boutput as\b", r"\breturn (?:a |an )?(?:list|json|dict|array)\b",
    r"\bplain text\b", r"\bcsv\b", r"\bxml\b",
]

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "clarity": {"type": "integer", "minimum": 0, "maximum": 100},
        "specificity": {"type": "integer", "minimum": 0, "maximum": 100},
        "hallucination_resistance": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": ["clarity", "specificity", "hallucination_resistance"],
}

SCORE_SYSTEM = (
    "You are an expert prompt evaluator. Score the given prompt on three dimensions from 0-100:\n"
    "- clarity: How unambiguous and clear is the instruction?\n"
    "- specificity: How specific and constrained is the task?\n"
    "- hallucination_resistance: Does the prompt instruct the model to ground its answer?\n"
    "Return ONLY a JSON object with these three integer fields."
)


class Scorer:
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def score(self, prompt: str) -> dict:
        token_efficiency = self._score_token_efficiency(prompt)
        format_control = self._score_format_control(prompt)
        llm_scores = self.adapter.call_structured_with_retry(
            SCORE_SYSTEM, f"Score this prompt:\n\n{prompt}", SCORE_SCHEMA
        )
        clarity = max(0, min(100, llm_scores["clarity"]))
        specificity = max(0, min(100, llm_scores["specificity"]))
        hr = max(0, min(100, llm_scores["hallucination_resistance"]))
        overall = int((token_efficiency + format_control + clarity + specificity + hr) / 5)
        return {
            "token_efficiency": token_efficiency,
            "format_control": format_control,
            "clarity": clarity,
            "specificity": specificity,
            "hallucination_resistance": hr,
            "overall": overall,
        }

    def _score_token_efficiency(self, prompt: str) -> int:
        count = len(self.tokenizer.encode(prompt)) if self.tokenizer else len(prompt) // 4
        return max(0, min(100, int(100 - (count - 1) / 5)))

    def _score_format_control(self, prompt: str) -> int:
        lower = prompt.lower()
        return min(100, sum(1 for p in FORMAT_PATTERNS if re.search(p, lower)) * 25)
```

- [ ] **Step 4: Run — expect all pass**

```bash
pytest tests/gepa/test_scorer.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_creator/gepa/scorer.py tests/gepa/test_scorer.py
git commit -m "feat: migrate scorer from MVP"
```

---

### Task 4: Loop spec (YAML schema)

**Files:**
- Create: `loop_creator/spec.py`
- Create: `tests/test_spec.py`

**Interfaces:**
- Produces:
  - `GEPAParams(population_size=5, top_k=2, max_generations=10, fitness_threshold=0.85, stagnation_limit=3, mutation_operators=[...])`
  - `GeneratorSpec(cli: str, model: str = "")`
  - `JudgeSpec(cli: str, rubric: str = "")`
  - `ContextSpec(project=True, history=True, external=[], mcp_auto_discover=True)`
  - `LoopSpec(id, type, task, goal, generator, judge, context, gepa)`
  - `load_spec(path: str) -> LoopSpec`
  - `save_spec(spec: LoopSpec, path: str) -> None`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_spec.py
import tempfile, os, yaml, pytest
from loop_creator.spec import LoopSpec, GeneratorSpec, JudgeSpec, ContextSpec, GEPAParams, load_spec, save_spec


MINIMAL_YAML = """
id: test-loop
type: coding
task: Fix the bug
goal: All tests pass
generator:
  cli: claude
judge:
  cli: ollama
"""


def test_load_spec_from_yaml(tmp_path):
    p = tmp_path / "loop.yaml"
    p.write_text(MINIMAL_YAML)
    spec = load_spec(str(p))
    assert spec.id == "test-loop"
    assert spec.type == "coding"
    assert spec.generator.cli == "claude"
    assert spec.judge.cli == "ollama"


def test_defaults_applied():
    p_data = {"id": "x", "type": "custom", "task": "t", "goal": "g",
               "generator": {"cli": "claude"}, "judge": {"cli": "claude"}}
    spec = LoopSpec(**p_data)
    assert spec.gepa.population_size == 5
    assert spec.gepa.top_k == 2
    assert spec.context.project is True


def test_save_and_reload(tmp_path):
    spec = LoopSpec(id="s1", type="coding", task="t", goal="g",
                    generator=GeneratorSpec(cli="claude"),
                    judge=JudgeSpec(cli="ollama"))
    path = str(tmp_path / "out.yaml")
    save_spec(spec, path)
    loaded = load_spec(path)
    assert loaded.id == "s1"
    assert loaded.generator.cli == "claude"


def test_invalid_type_raises():
    with pytest.raises(Exception):
        LoopSpec(id="x", type="invalid_type", task="t", goal="g",
                 generator=GeneratorSpec(cli="claude"),
                 judge=JudgeSpec(cli="claude"))
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/test_spec.py -v
```

- [ ] **Step 3: Create spec.py**

```python
# loop_creator/spec.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
import yaml

LOOP_TYPES = Literal["coding", "debugging", "docs", "rfc", "design", "prompt", "custom"]
MUTATION_OPS = Literal["rephrase", "expand", "constrain", "crossover"]


class GeneratorSpec(BaseModel):
    cli: str
    model: str = ""


class JudgeSpec(BaseModel):
    cli: str
    rubric: str = ""


class ContextSpec(BaseModel):
    project: bool = True
    history: bool = True
    external: list[str] = Field(default_factory=list)
    mcp_auto_discover: bool = True


class GEPAParams(BaseModel):
    population_size: int = 5
    top_k: int = 2
    max_generations: int = 10
    fitness_threshold: float = 0.85
    stagnation_limit: int = 3
    mutation_operators: list[MUTATION_OPS] = Field(
        default_factory=lambda: ["rephrase", "expand", "constrain", "crossover"]
    )


class LoopSpec(BaseModel):
    id: str
    type: LOOP_TYPES
    task: str
    goal: str
    generator: GeneratorSpec
    judge: JudgeSpec
    context: ContextSpec = Field(default_factory=ContextSpec)
    gepa: GEPAParams = Field(default_factory=GEPAParams)


def load_spec(path: str) -> LoopSpec:
    with open(path) as f:
        data = yaml.safe_load(f)
    return LoopSpec(**data)


def save_spec(spec: LoopSpec, path: str) -> None:
    with open(path, "w") as f:
        yaml.dump(spec.model_dump(), f, default_flow_style=False, sort_keys=False)
```

- [ ] **Step 4: Run — expect all pass**

```bash
pytest tests/test_spec.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_creator/spec.py tests/test_spec.py
git commit -m "feat: add LoopSpec YAML schema with load/save"
```

---

### Task 5: Judge module

**Files:**
- Create: `loop_creator/gepa/judge.py`
- Create: `tests/gepa/test_judge.py`

**Interfaces:**
- Produces: `Judge(adapter: LLMAdapter)` with `score(output: str, rubric: str) -> tuple[float, str]` — returns `(score_0_to_1, reason)`. On parse failure after 2 retries returns `(0.0, "parse failed")`.

- [ ] **Step 1: Write failing tests**

```python
# tests/gepa/test_judge.py
from unittest.mock import MagicMock
from loop_creator.gepa.judge import Judge
from loop_creator.adapters.base import LLMAdapter


class GoodAdapter(LLMAdapter):
    def call(self, s, u): return '{"score": 0.82, "reason": "Tests pass"}'
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


class BadAdapter(LLMAdapter):
    def call(self, s, u): return "no json here at all"
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


def test_score_returns_float_and_reason():
    score, reason = Judge(GoodAdapter()).score("output text", "Do tests pass?")
    assert score == 0.82
    assert reason == "Tests pass"


def test_score_clamped_to_0_1():
    class HighAdapter(LLMAdapter):
        def call(self, s, u): return '{"score": 1.5, "reason": "great"}'
        def call_structured(self, s, u, schema): return {}
        def is_available(self): return True
    score, _ = Judge(HighAdapter()).score("out", "rubric")
    assert score <= 1.0


def test_score_returns_zero_on_parse_failure():
    score, reason = Judge(BadAdapter()).score("out", "rubric")
    assert score == 0.0
    assert "parse failed" in reason


def test_rubric_injected_into_prompt():
    calls = []
    class RecordAdapter(LLMAdapter):
        def call(self, s, u):
            calls.append(u)
            return '{"score": 0.5, "reason": "ok"}'
        def call_structured(self, s, u, schema): return {}
        def is_available(self): return True
    Judge(RecordAdapter()).score("my output", "my rubric")
    assert "my rubric" in calls[0]
    assert "my output" in calls[0]
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/gepa/test_judge.py -v
```

- [ ] **Step 3: Create judge.py**

```python
# loop_creator/gepa/judge.py
import json
import re

from loop_creator.adapters.base import LLMAdapter

JUDGE_SYSTEM = (
    "You are an objective evaluator. Given an AI output and a rubric, score how well "
    "the output meets the rubric. Respond ONLY with a JSON object: "
    '{"score": <float 0.0-1.0>, "reason": "<one sentence>"}'
)


class Judge:
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter

    def score(self, output: str, rubric: str) -> tuple[float, str]:
        user = f"Rubric: {rubric}\n\nOutput to evaluate:\n{output}"
        for _ in range(3):
            try:
                raw = self.adapter.call(JUDGE_SYSTEM, user)
                match = re.search(r"\{.*?\}", raw, re.DOTALL)
                if not match:
                    continue
                data = json.loads(match.group())
                score = max(0.0, min(1.0, float(data["score"])))
                return score, str(data.get("reason", ""))
            except Exception:
                continue
        return 0.0, "parse failed"
```

- [ ] **Step 4: Run — expect all pass**

```bash
pytest tests/gepa/test_judge.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_creator/gepa/judge.py tests/gepa/test_judge.py
git commit -m "feat: add Judge module with rubric scoring and parse-failure fallback"
```

---

### Task 6: GEPA mutators

**Files:**
- Create: `loop_creator/gepa/mutators.py`
- Create: `tests/gepa/test_mutators.py`

**Interfaces:**
- Produces: `mutate(adapter: LLMAdapter, prompt: str, operator: str, context: str = "") -> str`
  - Operators: `"rephrase"`, `"expand"`, `"constrain"`, `"crossover"` (crossover takes two prompts joined by `\n---\n`)

- [ ] **Step 1: Write failing tests**

```python
# tests/gepa/test_mutators.py
from unittest.mock import MagicMock
from loop_creator.gepa.mutators import mutate
from loop_creator.adapters.base import LLMAdapter


class EchoAdapter(LLMAdapter):
    def call(self, s, u): return "mutated prompt result"
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


def test_rephrase_returns_string():
    result = mutate(EchoAdapter(), "original prompt", "rephrase")
    assert isinstance(result, str) and len(result) > 0


def test_expand_returns_string():
    result = mutate(EchoAdapter(), "original prompt", "expand")
    assert isinstance(result, str)


def test_constrain_returns_string():
    result = mutate(EchoAdapter(), "original prompt", "constrain")
    assert isinstance(result, str)


def test_crossover_requires_two_prompts_separated_by_delimiter():
    combined = "prompt A\n---\nprompt B"
    result = mutate(EchoAdapter(), combined, "crossover")
    assert isinstance(result, str)


def test_unknown_operator_raises():
    import pytest
    with pytest.raises(ValueError, match="Unknown operator"):
        mutate(EchoAdapter(), "prompt", "unknown_op")


def test_context_injected_when_provided():
    calls = []
    class RecordAdapter(LLMAdapter):
        def call(self, s, u):
            calls.append(u)
            return "result"
        def call_structured(self, s, u, schema): return {}
        def is_available(self): return True
    mutate(RecordAdapter(), "original", "rephrase", context="important context here")
    assert "important context here" in calls[0]
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/gepa/test_mutators.py -v
```

- [ ] **Step 3: Create mutators.py**

```python
# loop_creator/gepa/mutators.py
from loop_creator.adapters.base import LLMAdapter

_SYSTEMS = {
    "rephrase": (
        "Rewrite the prompt below using different wording while keeping the exact same intent. "
        "Return ONLY the rewritten prompt."
    ),
    "expand": (
        "Rewrite the prompt below by adding specificity, constraints, and output format instructions. "
        "Do not change the core intent. Return ONLY the rewritten prompt."
    ),
    "constrain": (
        "Rewrite the prompt below by trimming scope, removing ambiguity, and tightening focus. "
        "Return ONLY the rewritten prompt."
    ),
    "crossover": (
        "You are given two prompt variants separated by '---'. "
        "Splice the best elements from both into a single superior prompt. "
        "Return ONLY the combined prompt."
    ),
}


def mutate(adapter: LLMAdapter, prompt: str, operator: str, context: str = "") -> str:
    if operator not in _SYSTEMS:
        raise ValueError(f"Unknown operator: {operator!r}. Valid: {list(_SYSTEMS)}")
    system = _SYSTEMS[operator]
    ctx_block = f"\n\nProject context:\n{context}" if context else ""
    user = f"{prompt}{ctx_block}"
    return adapter.call(system, user).strip()
```

- [ ] **Step 4: Run — expect all pass**

```bash
pytest tests/gepa/test_mutators.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_creator/gepa/mutators.py tests/gepa/test_mutators.py
git commit -m "feat: add GEPA mutation operators (rephrase, expand, constrain, crossover)"
```

---

### Task 7: GEPA engine (extended)

**Files:**
- Create: `loop_creator/gepa/engine.py`
- Create: `tests/gepa/test_engine.py`

**Interfaces:**
- Consumes: `LLMAdapter`, `Judge`, `Scorer`, `GEPAParams`, `mutate()`
- Produces: `GEPAEngine(generator: LLMAdapter, judge: LLMAdapter, params: GEPAParams, scorer: Scorer | None = None)` with `run(task: str, goal: str, context: str = "") -> Generator[GenerationEvent, None, None]`
  - `GenerationEvent(generation: int, variants: list[Variant], best_score: float, event_type: str)`
  - `Variant(prompt: str, output: str, score: float, reason: str)`
  - `top_candidates(n=3) -> list[Variant]`

- [ ] **Step 1: Write failing tests**

```python
# tests/gepa/test_engine.py
from loop_creator.gepa.engine import GEPAEngine, GenerationEvent, Variant
from loop_creator.gepa.judge import Judge
from loop_creator.gepa.scorer import Scorer
from loop_creator.spec import GEPAParams
from loop_creator.adapters.base import LLMAdapter


class FakeAdapter(LLMAdapter):
    def __init__(self, output="result"):
        self._output = output
    def call(self, s, u): return self._output
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


class FakeJudge:
    def score(self, output, rubric): return (0.75, "looks good")


class FakeScorer:
    def score(self, prompt):
        return {"token_efficiency":80,"format_control":50,"clarity":70,
                "specificity":60,"hallucination_resistance":50,"overall":62}


def make_engine(pop=2, gens=2, threshold=0.99) -> GEPAEngine:
    params = GEPAParams(population_size=pop, top_k=1, max_generations=gens,
                        fitness_threshold=threshold, stagnation_limit=5)
    return GEPAEngine(
        generator=FakeAdapter("generated output"),
        judge=FakeJudge(),
        params=params,
    )


def test_run_yields_generation_events():
    engine = make_engine()
    events = list(engine.run("fix bug", "tests pass"))
    assert all(isinstance(e, GenerationEvent) for e in events)


def test_first_event_is_generation_0():
    events = list(make_engine().run("task", "goal"))
    assert events[0].generation == 0


def test_last_event_is_done():
    events = list(make_engine().run("task", "goal"))
    assert events[-1].event_type == "done"


def test_population_size_respected():
    engine = make_engine(pop=3, gens=1)
    events = list(engine.run("task", "goal"))
    gen1 = [e for e in events if e.generation == 1][0]
    assert len(gen1.variants) == 3


def test_stagnation_halts_early():
    params = GEPAParams(population_size=2, top_k=1, max_generations=10,
                        fitness_threshold=0.99, stagnation_limit=2)
    engine = GEPAEngine(generator=FakeAdapter(), judge=FakeJudge(), params=params)
    events = list(engine.run("task", "goal"))
    done = events[-1]
    assert done.event_type == "done"
    assert done.generation < 10


def test_top_candidates_returns_sorted():
    engine = make_engine(pop=2, gens=2)
    list(engine.run("task", "goal"))
    candidates = engine.top_candidates(3)
    scores = [c.score for c in candidates]
    assert scores == sorted(scores, reverse=True)
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/gepa/test_engine.py -v
```

- [ ] **Step 3: Create engine.py**

```python
# loop_creator/gepa/engine.py
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Generator

from loop_creator.adapters.base import LLMAdapter
from loop_creator.gepa.judge import Judge
from loop_creator.gepa.mutators import mutate
from loop_creator.spec import GEPAParams

SEED_SYSTEM = (
    "You are an expert AI agent. Given a task description and context, produce the best possible "
    "output for that task. Be specific, thorough, and complete."
)


@dataclass
class Variant:
    prompt: str
    output: str
    score: float
    reason: str
    generation: int = 0


@dataclass
class GenerationEvent:
    generation: int
    variants: list[Variant]
    best_score: float
    event_type: str = "generation"


class GEPAEngine:
    def __init__(self, generator: LLMAdapter, judge: Judge | object,
                 params: GEPAParams, scorer=None):
        self.generator = generator
        self.judge = judge
        self.params = params
        self.scorer = scorer
        self._all_variants: list[Variant] = []

    def run(self, task: str, goal: str, context: str = "") -> Generator[GenerationEvent, None, None]:
        ctx_block = f"\n\nContext:\n{context}" if context else ""

        # Generation 0: seed population
        seed_variants = []
        for i in range(self.params.population_size):
            prompt = f"Task: {task}{ctx_block}"
            output = self.generator.call(SEED_SYSTEM, prompt)
            score, reason = self.judge.score(output, goal)
            v = Variant(prompt=prompt, output=output, score=score, reason=reason, generation=0)
            seed_variants.append(v)
            self._all_variants.append(v)

        best_score = max(v.score for v in seed_variants)
        yield GenerationEvent(generation=0, variants=seed_variants, best_score=best_score)

        if best_score >= self.params.fitness_threshold:
            yield GenerationEvent(generation=0, variants=seed_variants,
                                  best_score=best_score, event_type="done")
            return

        stagnation = 0
        survivors = sorted(seed_variants, key=lambda v: v.score, reverse=True)[:self.params.top_k]

        for gen in range(1, self.params.max_generations + 1):
            new_variants = []
            ops = self.params.mutation_operators
            for i in range(self.params.population_size):
                parent = survivors[i % len(survivors)]
                op = ops[i % len(ops)]
                if op == "crossover" and len(survivors) >= 2:
                    combined = survivors[0].prompt + "\n---\n" + survivors[1].prompt
                    new_prompt = mutate(self.generator, combined, "crossover", context=context)
                else:
                    new_prompt = mutate(self.generator, parent.prompt, op, context=context)
                output = self.generator.call(SEED_SYSTEM, new_prompt)
                score, reason = self.judge.score(output, goal)
                v = Variant(prompt=new_prompt, output=output, score=score,
                            reason=reason, generation=gen)
                new_variants.append(v)
                self._all_variants.append(v)

            gen_best = max(v.score for v in new_variants)
            if gen_best <= best_score:
                stagnation += 1
            else:
                stagnation = 0
                best_score = gen_best

            yield GenerationEvent(generation=gen, variants=new_variants, best_score=best_score)

            if best_score >= self.params.fitness_threshold:
                break
            if stagnation >= self.params.stagnation_limit:
                break

            all_candidates = survivors + new_variants
            survivors = sorted(all_candidates, key=lambda v: v.score, reverse=True)[:self.params.top_k]

        best = max(self._all_variants, key=lambda v: v.score)
        yield GenerationEvent(generation=gen, variants=[best],
                              best_score=best.score, event_type="done")

    def top_candidates(self, n: int = 3) -> list[Variant]:
        return sorted(self._all_variants, key=lambda v: v.score, reverse=True)[:n]
```

- [ ] **Step 4: Run — expect all pass**

```bash
pytest tests/gepa/test_engine.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_creator/gepa/engine.py tests/gepa/test_engine.py
git commit -m "feat: add extended GEPA engine with population, stagnation, and threshold halting"
```

---

### Task 8: Context system

**Files:**
- Create: `loop_creator/context/project.py`
- Create: `loop_creator/context/history.py`
- Create: `loop_creator/context/external.py`
- Create: `loop_creator/context/mcp.py`
- Create: `loop_creator/context/bundle.py`
- Create: `tests/context/test_context.py`

**Interfaces:**
- Produces:
  - `scrape_project(root: str) -> str` — returns markdown summary of repo
  - `load_history_summary(loop_dir: str) -> str` — top/bottom 3 from history.jsonl
  - `append_history(loop_dir: str, event: dict) -> None`
  - `load_external(paths: list[str]) -> str` — reads files, fetches URLs
  - `discover_mcp_servers() -> list[str]` — server names from `~/.claude/settings.json`
  - `build_bundle(project="", history="", external="", token_budget=8000) -> str`

- [ ] **Step 1: Write failing tests**

```python
# tests/context/test_context.py
import json, os, tempfile
from loop_creator.context.project import scrape_project
from loop_creator.context.history import append_history, load_history_summary
from loop_creator.context.external import load_external
from loop_creator.context.bundle import build_bundle


def test_scrape_project_returns_string(tmp_path):
    (tmp_path / "README.md").write_text("# My Project")
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"')
    result = scrape_project(str(tmp_path))
    assert "README" in result or "pyproject" in result


def test_append_and_load_history(tmp_path):
    loop_dir = str(tmp_path)
    append_history(loop_dir, {"generation": 1, "score": 0.8, "prompt": "p1", "reason": "good"})
    append_history(loop_dir, {"generation": 2, "score": 0.5, "prompt": "p2", "reason": "ok"})
    summary = load_history_summary(loop_dir)
    assert "0.8" in summary or "p1" in summary


def test_load_external_reads_file(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Design Doc\nImportant details here.")
    result = load_external([str(f)])
    assert "Important details here" in result


def test_load_external_skips_missing_file():
    result = load_external(["/nonexistent/path.md"])
    assert "not found" in result.lower() or result == ""


def test_build_bundle_joins_sections():
    result = build_bundle(project="proj info", history="hist info", external="ext info")
    assert "proj info" in result
    assert "hist info" in result
    assert "ext info" in result


def test_build_bundle_respects_token_budget():
    big = "word " * 10000
    result = build_bundle(project=big, token_budget=500)
    assert len(result.split()) <= 600
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/context/test_context.py -v
```

- [ ] **Step 3: Create project.py**

```python
# loop_creator/context/project.py
import os
import subprocess

KEY_FILES = ["README.md", "pyproject.toml", "package.json", "go.mod",
             "Cargo.toml", "CLAUDE.md", ".env.example", "requirements.txt"]


def scrape_project(root: str) -> str:
    lines = ["## Project Context\n"]
    # Directory tree (max depth 3, exclude common noise)
    tree = _tree(root, max_depth=3)
    lines.append(f"### Directory Tree\n```\n{tree}\n```\n")
    # Key files
    for fname in KEY_FILES:
        path = os.path.join(root, fname)
        if os.path.isfile(path):
            try:
                content = open(path).read()[:2000]
                lines.append(f"### {fname}\n```\n{content}\n```\n")
            except Exception:
                pass
    # Git info
    git_info = _git_info(root)
    if git_info:
        lines.append(f"### Git\n{git_info}\n")
    return "\n".join(lines)


def _tree(root: str, max_depth: int) -> str:
    SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".loop-creator"}
    lines = []
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.replace(root, "").count(os.sep)
        if depth >= max_depth:
            dirnames.clear()
            continue
        dirnames[:] = [d for d in sorted(dirnames) if d not in SKIP]
        indent = "  " * depth
        lines.append(f"{indent}{os.path.basename(dirpath)}/")
        for f in sorted(filenames)[:20]:
            lines.append(f"{indent}  {f}")
    return "\n".join(lines[:100])


def _git_info(root: str) -> str:
    try:
        branch = subprocess.check_output(
            ["git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL, text=True).strip()
        log = subprocess.check_output(
            ["git", "-C", root, "log", "--oneline", "-5"],
            stderr=subprocess.DEVNULL, text=True).strip()
        return f"Branch: {branch}\nRecent commits:\n{log}"
    except Exception:
        return ""
```

- [ ] **Step 4: Create history.py**

```python
# loop_creator/context/history.py
import json
import os


def append_history(loop_dir: str, event: dict) -> None:
    os.makedirs(loop_dir, exist_ok=True)
    path = os.path.join(loop_dir, "history.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")


def load_history_summary(loop_dir: str) -> str:
    path = os.path.join(loop_dir, "history.jsonl")
    if not os.path.isfile(path):
        return ""
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    if not entries:
        return ""
    sorted_entries = sorted(entries, key=lambda e: e.get("score", 0), reverse=True)
    top = sorted_entries[:3]
    bottom = sorted_entries[-3:]
    lines = ["## Prior Iteration History\n### Top performers:"]
    for e in top:
        lines.append(f"- Gen {e.get('generation','?')} score={e.get('score','?')}: {str(e.get('prompt',''))[:80]}")
    lines.append("### Lowest performers:")
    for e in bottom:
        lines.append(f"- Gen {e.get('generation','?')} score={e.get('score','?')}: {str(e.get('prompt',''))[:80]}")
    return "\n".join(lines)
```

- [ ] **Step 5: Create external.py**

```python
# loop_creator/context/external.py
import os


def load_external(paths: list[str]) -> str:
    parts = []
    for path in paths:
        if path.startswith("http://") or path.startswith("https://"):
            try:
                import httpx
                resp = httpx.get(path, timeout=10.0, follow_redirects=True)
                parts.append(f"### {path}\n{resp.text[:3000]}")
            except Exception as e:
                parts.append(f"### {path}\n[fetch failed: {e}]")
        elif os.path.isfile(path):
            try:
                content = open(path).read()[:3000]
                parts.append(f"### {os.path.basename(path)}\n{content}")
            except Exception as e:
                parts.append(f"### {path}\n[read failed: {e}]")
        else:
            parts.append(f"### {path}\n[not found]")
    return "\n\n".join(parts)
```

- [ ] **Step 6: Create mcp.py**

```python
# loop_creator/context/mcp.py
import json
import os


def discover_mcp_servers() -> list[str]:
    candidates = [
        os.path.expanduser("~/.claude/settings.json"),
        os.path.join(os.getcwd(), ".claude", "settings.json"),
    ]
    names = []
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            data = json.load(open(path))
            servers = data.get("mcpServers", {})
            for name in servers:
                if name not in names:
                    names.append(name)
        except Exception:
            pass
    return names
```

- [ ] **Step 7: Create bundle.py**

```python
# loop_creator/context/bundle.py


def build_bundle(project: str = "", history: str = "", external: str = "",
                 token_budget: int = 8000) -> str:
    sections = []
    if project:
        sections.append(project)
    if history:
        sections.append(history)
    if external:
        sections.append(f"## External Context\n{external}")
    combined = "\n\n".join(sections)
    # Trim to token budget (approx 4 chars/token)
    max_chars = token_budget * 4
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[... context trimmed to token budget ...]"
    return combined
```

- [ ] **Step 8: Run — expect all pass**

```bash
pytest tests/context/test_context.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 9: Commit**

```bash
git add loop_creator/context/ tests/context/
git commit -m "feat: add context system (project, history, external, MCP, bundle)"
```

---

### Task 9: Loop type registry

**Files:**
- Create: `loop_creator/loop_types/registry.py`
- Create: `tests/loop_types/test_registry.py`

**Interfaces:**
- Produces: `get_loop_type(type_name: str) -> LoopTypeConfig`
  - `LoopTypeConfig(name, judge_rubric_template, context_hints: list[str], default_gepa: dict)`
  - `LoopTypeConfig.rubric(goal: str) -> str` — fills `{goal}` into template

- [ ] **Step 1: Write failing tests**

```python
# tests/loop_types/test_registry.py
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
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/loop_types/test_registry.py -v
```

- [ ] **Step 3: Create registry.py**

```python
# loop_creator/loop_types/registry.py
from dataclasses import dataclass, field


@dataclass
class LoopTypeConfig:
    name: str
    judge_rubric_template: str
    context_hints: list[str]
    default_population_size: int = 5
    default_max_generations: int = 10
    default_fitness_threshold: float = 0.85
    uses_scorer: bool = False

    def rubric(self, goal: str) -> str:
        return self.judge_rubric_template.replace("{goal}", goal)


_REGISTRY: dict[str, LoopTypeConfig] = {
    "coding": LoopTypeConfig(
        name="coding",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the output achieve the following goal? '{goal}' "
            "Is the code minimal, clean, and correct? 1.0 = fully achieves goal with clean code."
        ),
        context_hints=["*.py", "*.ts", "*.go", "*.rs", "test_*", "*.test.*", "*.spec.*"],
    ),
    "debugging": LoopTypeConfig(
        name="debugging",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the output correctly identify and fix the issue described in '{goal}'? "
            "Is the root cause explained? Is the fix minimal with no regression risk?"
        ),
        context_hints=["*.log", "*.py", "*.ts", "traceback*", "error*"],
    ),
    "docs": LoopTypeConfig(
        name="docs",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the documentation output satisfy '{goal}'? "
            "Is it accurate, complete, and readable by a new contributor?"
        ),
        context_hints=["README*", "*.md", "docs/", "*.py", "*.ts"],
    ),
    "rfc": LoopTypeConfig(
        name="rfc",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the RFC draft satisfy '{goal}'? "
            "Does it cover: motivation, proposed design, alternatives considered, trade-offs, open questions?"
        ),
        context_hints=["docs/", "*.md", "rfcs/"],
        default_max_generations=8,
    ),
    "design": LoopTypeConfig(
        name="design",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the design document satisfy '{goal}'? "
            "Are components clearly bounded with well-defined interfaces and data flows?"
        ),
        context_hints=["docs/", "*.md", "src/", "*.py", "*.ts"],
    ),
    "prompt": LoopTypeConfig(
        name="prompt",
        judge_rubric_template=(
            "Score 0.0–1.0: Is this prompt clear, specific, grounded, token-efficient, and well-formatted? "
            "Goal: '{goal}'"
        ),
        context_hints=[],
        uses_scorer=True,
        default_population_size=3,
        default_max_generations=5,
    ),
    "custom": LoopTypeConfig(
        name="custom",
        judge_rubric_template="{goal}",
        context_hints=[],
    ),
}


def get_loop_type(type_name: str) -> LoopTypeConfig:
    return _REGISTRY[type_name]
```

- [ ] **Step 4: Run — expect all pass**

```bash
pytest tests/loop_types/test_registry.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_creator/loop_types/registry.py tests/loop_types/test_registry.py
git commit -m "feat: add loop type registry with 7 built-in types"
```

---

### Task 10: Adapter factory + runner

**Files:**
- Create: `loop_creator/runner.py`
- Create: `tests/test_runner.py`

**Interfaces:**
- Consumes: `LoopSpec`, `GEPAEngine`, context system, loop type registry
- Produces:
  - `build_adapter(cli: str, model: str = "") -> LLMAdapter` — returns correct adapter for the cli string
  - `detect_available_adapters() -> list[str]` — returns list of available cli names
  - `run_loop(spec: LoopSpec, loop_dir: str, on_event=None) -> Variant` — runs full loop, saves best.md, calls `on_event(GenerationEvent)` if provided, returns best variant

- [ ] **Step 1: Write failing tests**

```python
# tests/test_runner.py
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
         patch("loop_creator.adapters.devin.shutil.which", return_value=None):
        result = detect_available_adapters()
    assert isinstance(result, list)
    assert "claude" in result
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/test_runner.py -v
```

- [ ] **Step 3: Create runner.py**

```python
# loop_creator/runner.py
from __future__ import annotations
import os

from loop_creator.adapters.base import LLMAdapter
from loop_creator.adapters.claude import ClaudeAdapter
from loop_creator.adapters.ollama import OllamaAdapter
from loop_creator.adapters.devin import DevinAdapter
from loop_creator.context.project import scrape_project
from loop_creator.context.history import load_history_summary, append_history
from loop_creator.context.external import load_external
from loop_creator.context.bundle import build_bundle
from loop_creator.gepa.engine import GEPAEngine, GenerationEvent, Variant
from loop_creator.gepa.judge import Judge
from loop_creator.gepa.scorer import Scorer
from loop_creator.loop_types.registry import get_loop_type
from loop_creator.spec import LoopSpec


def build_adapter(cli: str, model: str = "") -> LLMAdapter:
    if cli == "claude":
        return ClaudeAdapter(model=model or "sonnet")
    if cli == "ollama":
        return OllamaAdapter(model=model or "llama3.2")
    if cli == "devin":
        return DevinAdapter()
    raise ValueError(f"Unknown CLI: {cli!r}. Supported: claude, ollama, devin")


def detect_available_adapters() -> list[str]:
    adapters = [
        ("claude", ClaudeAdapter()),
        ("ollama", OllamaAdapter()),
        ("devin", DevinAdapter()),
    ]
    return [name for name, a in adapters if a.is_available()]


def run_loop(
    spec: LoopSpec,
    loop_dir: str,
    on_event=None,
) -> Variant:
    os.makedirs(loop_dir, exist_ok=True)
    loop_type = get_loop_type(spec.type)

    generator = build_adapter(spec.generator.cli, spec.generator.model)
    judge_adapter = build_adapter(spec.judge.cli)
    judge = Judge(judge_adapter)

    scorer = None
    if loop_type.uses_scorer:
        scorer = Scorer(judge_adapter)

    # Build context bundle
    ctx_parts = {}
    if spec.context.project:
        ctx_parts["project"] = scrape_project(os.getcwd())
    if spec.context.history:
        ctx_parts["history"] = load_history_summary(loop_dir)
    if spec.context.external:
        ctx_parts["external"] = load_external(spec.context.external)
    context = build_bundle(**ctx_parts)

    goal = spec.goal
    if not spec.judge.rubric:
        goal = loop_type.rubric(spec.goal)

    engine = GEPAEngine(generator=generator, judge=judge, params=spec.gepa, scorer=scorer)

    best: Variant | None = None
    for event in engine.run(task=spec.task, goal=goal, context=context):
        if on_event:
            on_event(event)
        if event.event_type == "done":
            best = event.variants[0]
            for v in event.variants:
                append_history(loop_dir, {
                    "generation": v.generation, "score": v.score,
                    "prompt": v.prompt[:200], "reason": v.reason,
                })

    if best is None:
        best = engine.top_candidates(1)[0]

    best_path = os.path.join(loop_dir, "best.md")
    with open(best_path, "w") as f:
        f.write(f"# Best Result\n\nScore: {best.score:.3f}\nReason: {best.reason}\n\n## Output\n\n{best.output}\n\n## Prompt\n\n{best.prompt}\n")

    return best
```

- [ ] **Step 4: Run — expect all pass**

```bash
pytest tests/test_runner.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_creator/runner.py tests/test_runner.py
git commit -m "feat: add runner with adapter factory and full loop orchestration"
```

---

### Task 11: Typer CLI

**Files:**
- Create: `loop_creator/cli.py`
- Test: manual smoke test (CLI is hard to unit-test; rely on integration)

**Interfaces:**
- Consumes: `load_spec`, `save_spec`, `run_loop`, `detect_available_adapters`
- Produces: `loop-creator` entry point with commands: `new`, `run`, `ls`, `history`, `best`, `context`

- [ ] **Step 1: Create cli.py**

```python
# loop_creator/cli.py
from __future__ import annotations
import os
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from loop_creator.runner import run_loop, detect_available_adapters
from loop_creator.spec import load_spec, save_spec, LoopSpec, GeneratorSpec, JudgeSpec
from loop_creator.context.history import load_history_summary

app = typer.Typer(help="loop-creator — build and run GEPA-powered AI dev loops")
console = Console()

LOOPS_DIR = "loops"
STATE_DIR = ".loop-creator"


def _loop_dir(loop_id: str) -> str:
    return os.path.join(STATE_DIR, loop_id)


def _loop_spec_path(loop_id: str) -> str:
    return os.path.join(LOOPS_DIR, f"{loop_id}.yaml")


@app.command()
def new():
    """Launch the interactive wizard to build a new loop."""
    from loop_creator.wizard.app import WizardApp
    result = WizardApp().run()
    if result:
        os.makedirs(LOOPS_DIR, exist_ok=True)
        path = _loop_spec_path(result.id)
        save_spec(result, path)
        console.print(f"[green]Loop saved to {path}[/green]")
        if typer.confirm("Run it now?"):
            _do_run(result)


@app.command()
def run(
    spec_path: str = typer.Argument(..., help="Path to loop spec YAML"),
    watch: bool = typer.Option(False, "--watch", help="Show live TUI dashboard"),
):
    """Run a loop from a YAML spec file."""
    spec = load_spec(spec_path)
    _do_run(spec, watch=watch)


@app.command(name="ls")
def list_loops():
    """List all saved loops."""
    loops_path = Path(LOOPS_DIR)
    if not loops_path.exists():
        console.print("[yellow]No loops saved yet. Run 'loop-creator new' to create one.[/yellow]")
        return
    table = Table(title="Saved Loops")
    table.add_column("ID"); table.add_column("Type"); table.add_column("Task"); table.add_column("Best Score")
    for f in sorted(loops_path.glob("*.yaml")):
        spec = load_spec(str(f))
        best_path = os.path.join(_loop_dir(spec.id), "best.md")
        score = "—"
        if os.path.isfile(best_path):
            for line in open(best_path):
                if line.startswith("Score:"):
                    score = line.split(":", 1)[1].strip()
                    break
        table.add_row(spec.id, spec.type, spec.task[:50], score)
    console.print(table)


@app.command()
def history(loop_id: str = typer.Argument(..., help="Loop ID")):
    """Show evolution history for a loop."""
    summary = load_history_summary(_loop_dir(loop_id))
    if not summary:
        console.print(f"[yellow]No history found for loop '{loop_id}'[/yellow]")
        return
    console.print(Panel(summary, title=f"History: {loop_id}"))


@app.command()
def best(loop_id: str = typer.Argument(..., help="Loop ID")):
    """Print the best result for a loop."""
    path = os.path.join(_loop_dir(loop_id), "best.md")
    if not os.path.isfile(path):
        console.print(f"[red]No best result found for '{loop_id}'. Has this loop been run?[/red]")
        raise typer.Exit(1)
    console.print(open(path).read())


@app.command()
def context(loop_id: str = typer.Argument(..., help="Loop ID")):
    """Open the context editor for a loop."""
    from loop_creator.wizard.app import ContextEditorApp
    spec_path = _loop_spec_path(loop_id)
    if not os.path.isfile(spec_path):
        console.print(f"[red]Loop '{loop_id}' not found at {spec_path}[/red]")
        raise typer.Exit(1)
    spec = load_spec(spec_path)
    updated = ContextEditorApp(spec).run()
    if updated:
        save_spec(updated, spec_path)
        console.print(f"[green]Context updated for {loop_id}[/green]")


def _do_run(spec: LoopSpec, watch: bool = False):
    loop_dir = _loop_dir(spec.id)
    available = detect_available_adapters()
    if spec.generator.cli not in available:
        console.print(f"[red]Generator CLI '{spec.generator.cli}' not available. Available: {available}[/red]")
        raise typer.Exit(1)
    if spec.judge.cli not in available:
        console.print(f"[red]Judge CLI '{spec.judge.cli}' not available. Available: {available}[/red]")
        raise typer.Exit(1)

    if watch:
        from loop_creator.wizard.dashboard import DashboardApp
        DashboardApp(spec=spec, loop_dir=loop_dir).run()
    else:
        from rich.progress import Progress, SpinnerColumn, TextColumn
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(f"Running loop: {spec.id}", total=spec.gepa.max_generations)

            def on_event(event):
                progress.update(task, advance=1,
                    description=f"Gen {event.generation}/{spec.gepa.max_generations} · Best: {event.best_score:.2f}")

            best_variant = run_loop(spec, loop_dir, on_event=on_event)

        console.print(Panel(
            f"Score: [green]{best_variant.score:.3f}[/green]\nReason: {best_variant.reason}\n\n{best_variant.output[:500]}",
            title=f"[bold]Best Result — {spec.id}[/bold]"
        ))
        console.print(f"Full result saved to [cyan]{loop_dir}/best.md[/cyan]")


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Smoke test CLI is importable**

```bash
cd /Users/avinashvundyala/Documents/github/skills
python -c "from loop_creator.cli import app; print('CLI OK')"
```

Expected: `CLI OK`

- [ ] **Step 3: Smoke test help output**

```bash
loop-creator --help
```

Expected: shows `new`, `run`, `ls`, `history`, `best`, `context` commands.

- [ ] **Step 4: Commit**

```bash
git add loop_creator/cli.py
git commit -m "feat: add Typer CLI with new/run/ls/history/best/context commands"
```

---

### Task 12: Textual wizard

**Files:**
- Create: `loop_creator/wizard/app.py`
- Create: `loop_creator/wizard/screens/loop_type.py`
- Create: `loop_creator/wizard/screens/task.py`
- Create: `loop_creator/wizard/screens/goal.py`
- Create: `loop_creator/wizard/screens/context_screen.py`
- Create: `loop_creator/wizard/screens/cli_select.py`
- Create: `loop_creator/wizard/screens/gepa_params.py`
- Create: `loop_creator/wizard/screens/preview.py`
- Create: `loop_creator/wizard/dashboard.py`

**Interfaces:**
- Consumes: `LoopSpec`, `detect_available_adapters`, `scrape_project`, `discover_mcp_servers`
- Produces: `WizardApp().run() -> LoopSpec | None`, `DashboardApp(spec, loop_dir).run()`, `ContextEditorApp(spec).run() -> LoopSpec | None`

- [ ] **Step 1: Create wizard/app.py**

```python
# loop_creator/wizard/app.py
from __future__ import annotations
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from loop_creator.spec import LoopSpec, GeneratorSpec, JudgeSpec, ContextSpec, GEPAParams
from loop_creator.runner import detect_available_adapters
from loop_creator.wizard.screens.loop_type import LoopTypeScreen
from loop_creator.wizard.screens.task import TaskScreen
from loop_creator.wizard.screens.goal import GoalScreen
from loop_creator.wizard.screens.context_screen import ContextScreen
from loop_creator.wizard.screens.cli_select import CLISelectScreen
from loop_creator.wizard.screens.gepa_params import GEPAParamsScreen
from loop_creator.wizard.screens.preview import PreviewScreen


class WizardApp(App):
    CSS = """
    Screen { background: $surface; }
    .title { color: $accent; text-style: bold; margin-bottom: 1; }
    .tip { color: $text-muted; margin-top: 1; }
    .step-bar { dock: top; height: 1; background: $panel; }
    """
    TITLE = "loop-creator wizard"
    BINDINGS = [("escape", "back", "Back"), ("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self._result: LoopSpec | None = None
        self._state: dict = {}
        self._available = detect_available_adapters()

    def on_mount(self):
        self.push_screen(LoopTypeScreen(), self._on_loop_type)

    def _on_loop_type(self, loop_type: str):
        self._state["type"] = loop_type
        self.push_screen(TaskScreen(loop_type), self._on_task)

    def _on_task(self, task: str):
        self._state["task"] = task
        self.push_screen(GoalScreen(self._state["type"], task), self._on_goal)

    def _on_goal(self, goal: str):
        self._state["goal"] = goal
        self.push_screen(ContextScreen(self._state["task"]), self._on_context)

    def _on_context(self, context_spec: ContextSpec):
        self._state["context"] = context_spec
        self.push_screen(CLISelectScreen(self._available), self._on_cli)

    def _on_cli(self, cli_pair: tuple[str, str]):
        gen_cli, judge_cli = cli_pair
        self._state["generator"] = GeneratorSpec(cli=gen_cli)
        self._state["judge"] = JudgeSpec(cli=judge_cli)
        self.push_screen(GEPAParamsScreen(self._state["type"]), self._on_gepa)

    def _on_gepa(self, params: GEPAParams):
        self._state["gepa"] = params
        import re, time
        loop_id = re.sub(r"[^a-z0-9-]", "-", self._state["task"][:30].lower()).strip("-")
        loop_id = loop_id or f"loop-{int(time.time())}"
        spec = LoopSpec(
            id=loop_id,
            type=self._state["type"],
            task=self._state["task"],
            goal=self._state["goal"],
            generator=self._state["generator"],
            judge=self._state["judge"],
            context=self._state["context"],
            gepa=self._state["gepa"],
        )
        self.push_screen(PreviewScreen(spec), self._on_preview)

    def _on_preview(self, spec: LoopSpec | None):
        self._result = spec
        self.exit(spec)

    def action_back(self):
        if len(self.screen_stack) > 1:
            self.pop_screen()


class ContextEditorApp(App):
    TITLE = "loop-creator context editor"

    def __init__(self, spec: LoopSpec):
        super().__init__()
        self._spec = spec
        self._result: LoopSpec | None = None

    def on_mount(self):
        self.push_screen(ContextScreen(self._spec.task, initial=self._spec.context), self._on_done)

    def _on_done(self, context_spec: ContextSpec):
        self._result = self._spec.model_copy(update={"context": context_spec})
        self.exit(self._result)
```

- [ ] **Step 2: Create wizard screens (all 7)**

Create `loop_creator/wizard/screens/loop_type.py`:

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label
from textual.binding import Binding

LOOP_TYPES = [
    ("coding",    "Fix, implement, or refactor code"),
    ("debugging", "Track down and resolve a bug"),
    ("docs",      "Write or improve documentation"),
    ("rfc",       "Draft a structured RFC or proposal"),
    ("design",    "Architecture and system design docs"),
    ("prompt",    "Iteratively improve a prompt"),
    ("custom",    "Define your own loop from scratch"),
]

TIPS = {
    "coding": "Works well for targeted tasks like 'migrate all fetch calls to axios'",
    "debugging": "Tip: include error logs in your context for best results",
    "docs": "Tip: add the source file to context so the doc matches the code",
    "rfc": "Tip: attach prior RFCs as external context for consistent format",
    "design": "Tip: add existing architecture docs to context",
    "prompt": "Uses multi-dimensional scoring — no judge CLI needed",
    "custom": "You define the goal and rubric entirely",
}


class LoopTypeScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Step 1/7 · Loop Type\n\nWhat kind of loop are you building?\nThis shapes how context is gathered and how the judge evaluates outputs.", classes="title")
        yield ListView(
            *[ListItem(Label(f"  {name:<12} {desc}"), id=name) for name, desc in LOOP_TYPES],
            id="type-list"
        )
        yield Static("", id="tip", classes="tip")
        yield Footer()

    def on_list_view_highlighted(self, event: ListView.Highlighted):
        if event.item:
            t = TIPS.get(event.item.id, "")
            self.query_one("#tip", Static).update(f"Tip: {t}")

    def on_list_view_selected(self, event: ListView.Selected):
        self.dismiss(event.item.id)
```

Create `loop_creator/wizard/screens/task.py`:

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding

EXAMPLES = {
    "coding": "e.g. 'Fix the JWT expiry bug causing 401s after token refresh'",
    "debugging": "e.g. 'Find why the payment service returns 500 on checkout'",
    "docs": "e.g. 'Write a README for the auth module'",
    "rfc": "e.g. 'Draft an RFC for migrating from REST to GraphQL'",
    "design": "e.g. 'Design the caching layer for the API gateway'",
    "prompt": "e.g. 'Improve this prompt: Summarize the document'",
    "custom": "e.g. 'Generate 10 unit test cases for the payment module'",
}


class TaskScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, loop_type: str):
        super().__init__()
        self._loop_type = loop_type

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Step 2/7 · Task Description\n\nDescribe what you want the loop to accomplish.\n{EXAMPLES.get(self._loop_type, '')}", classes="title")
        yield Input(placeholder="Enter task description...", id="task-input")
        yield Static("", id="validation", classes="tip")
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_input_changed(self, event: Input.Changed):
        if len(event.value.strip()) < 10:
            self.query_one("#validation", Static).update("[yellow]Be specific — longer descriptions produce better loops[/yellow]")
        else:
            self.query_one("#validation", Static).update("[green]✓[/green]")

    def on_button_pressed(self, event: Button.Pressed):
        val = self.query_one("#task-input", Input).value.strip()
        if len(val) < 3:
            self.query_one("#validation", Static).update("[red]Task description is required[/red]")
            return
        self.dismiss(val)
```

Create `loop_creator/wizard/screens/goal.py`:

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding

GOAL_EXAMPLES = {
    "coding": "e.g. 'All auth integration tests pass, no 401 errors in logs'",
    "debugging": "e.g. 'Root cause identified, fix applied, all tests green'",
    "docs": "e.g. 'README covers installation, usage, and all public API methods'",
    "rfc": "e.g. 'RFC covers motivation, design, alternatives, and trade-offs'",
    "design": "e.g. 'All components have clear boundaries and defined interfaces'",
    "prompt": "e.g. 'Score ≥85 on clarity, specificity, and hallucination resistance'",
    "custom": "e.g. 'Output matches the acceptance criteria defined in the ticket'",
}


class GoalScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, loop_type: str, task: str):
        super().__init__()
        self._loop_type = loop_type
        self._task = task

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Step 3/7 · Success Goal\n\nWhat does 'done' look like for this loop?\n"
            f"This becomes the judge's rubric.\n{GOAL_EXAMPLES.get(self._loop_type, '')}",
            classes="title"
        )
        yield Input(placeholder="Enter success criteria...", id="goal-input")
        yield Static("[dim]Tip: Be measurable. 'Tests pass' is better than 'looks good'.[/dim]", classes="tip")
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        val = self.query_one("#goal-input", Input).value.strip()
        if len(val) < 3:
            return
        self.dismiss(val)
```

Create `loop_creator/wizard/screens/context_screen.py`:

```python
from __future__ import annotations
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Checkbox, Input, Button, ListView, ListItem, Label
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from loop_creator.spec import ContextSpec
from loop_creator.context.mcp import discover_mcp_servers
from loop_creator.context.project import scrape_project
import os


class ContextScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, task: str, initial: ContextSpec | None = None):
        super().__init__()
        self._task = task
        self._initial = initial or ContextSpec()
        self._mcp_servers = discover_mcp_servers()
        self._external_paths: list[str] = list(self._initial.external)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Step 4/7 · Context\n\nToggle sources with Space, add new with the input below.\n"
            "The more relevant context, the better the loop performs.",
            classes="title"
        )
        yield Checkbox("Project files (auto-detected)", value=self._initial.project, id="ctx-project")
        yield Checkbox("Iteration history (what worked/failed before)", value=self._initial.history, id="ctx-history")
        yield Static("[dim]── External ──[/dim]")
        for path in self._external_paths:
            yield Static(f"  ✓ {path}")
        yield Input(placeholder="Add file path or URL...", id="external-input")
        if self._mcp_servers:
            yield Static("[dim]── MCP Servers (auto-discovered) ──[/dim]")
            for name in self._mcp_servers:
                yield Checkbox(f"MCP: {name}", value=False, id=f"mcp-{name}")
        yield Static("", id="token-budget", classes="tip")
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_mount(self):
        self._update_budget()

    def _update_budget(self):
        estimate = 500
        if self.query_one("#ctx-project", Checkbox).value:
            estimate += 2000
        estimate += len(self._external_paths) * 500
        self.query_one("#token-budget", Static).update(
            f"[dim]Estimated context: ~{estimate:,} / 8,000 tokens[/dim]"
        )

    def on_checkbox_changed(self, event: Checkbox.Changed):
        self._update_budget()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "next":
            ext_input = self.query_one("#external-input", Input).value.strip()
            if ext_input:
                self._external_paths.append(ext_input)
            spec = ContextSpec(
                project=self.query_one("#ctx-project", Checkbox).value,
                history=self.query_one("#ctx-history", Checkbox).value,
                external=self._external_paths,
                mcp_auto_discover=True,
            )
            self.dismiss(spec)
```

Create `loop_creator/wizard/screens/cli_select.py`:

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Select, Button
from textual.binding import Binding


class CLISelectScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, available: list[str]):
        super().__init__()
        self._available = available

    def compose(self) -> ComposeResult:
        if not self._available:
            yield Static("[red]No CLI tools detected. Install claude, devin, or ollama first.[/red]")
            return
        yield Header()
        opts = [(cli, cli) for cli in self._available]
        yield Static(
            "Step 5/7 · CLI Selection\n\nChoose which tool generates outputs and which judges them.\n"
            "Tip: use a fast/cheap model to generate, a smart model to judge.",
            classes="title"
        )
        yield Static("Generator (produces loop outputs):")
        yield Select(opts, id="gen-select", value=self._available[0])
        yield Static("Judge (scores outputs against your goal):")
        yield Select(opts, id="judge-select", value=self._available[-1])
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        gen = self.query_one("#gen-select", Select).value
        judge = self.query_one("#judge-select", Select).value
        self.dismiss((str(gen), str(judge)))
```

Create `loop_creator/wizard/screens/gepa_params.py`:

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding
from loop_creator.spec import GEPAParams
from loop_creator.loop_types.registry import get_loop_type


class GEPAParamsScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, loop_type: str):
        super().__init__()
        self._defaults = get_loop_type(loop_type)

    def compose(self) -> ComposeResult:
        d = self._defaults
        yield Header()
        yield Static(
            "Step 6/7 · GEPA Parameters\n\nTune the evolutionary search. Defaults are good for most loops.\n"
            "Press Next to accept defaults.",
            classes="title"
        )
        yield Static(f"Population size (variants per generation) — default {d.default_population_size}:")
        yield Input(str(d.default_population_size), id="pop-input")
        yield Static(f"Max generations — default {d.default_max_generations}:")
        yield Input(str(d.default_max_generations), id="gen-input")
        yield Static(f"Fitness threshold (0.0–1.0, halt when reached) — default {d.default_fitness_threshold}:")
        yield Input(str(d.default_fitness_threshold), id="thresh-input")
        yield Static("[dim]Tip: lower threshold = faster but lower quality. Higher = more iterations.[/dim]", classes="tip")
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        try:
            pop = int(self.query_one("#pop-input", Input).value)
            gens = int(self.query_one("#gen-input", Input).value)
            thresh = float(self.query_one("#thresh-input", Input).value)
        except ValueError:
            return
        params = GEPAParams(
            population_size=max(1, pop),
            max_generations=max(1, gens),
            fitness_threshold=max(0.0, min(1.0, thresh)),
        )
        self.dismiss(params)
```

Create `loop_creator/wizard/screens/preview.py`:

```python
import yaml
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
from loop_creator.spec import LoopSpec


class PreviewScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, spec: LoopSpec):
        super().__init__()
        self._spec = spec

    def compose(self) -> ComposeResult:
        yaml_str = yaml.dump(self._spec.model_dump(), default_flow_style=False, sort_keys=False)
        yield Header()
        yield Static("Step 7/7 · Preview & Launch\n\nYour loop spec:", classes="title")
        yield Static(f"```yaml\n{yaml_str}\n```")
        yield Button("Save & Run", id="run", variant="success")
        yield Button("Save only", id="save", variant="primary")
        yield Button("← Back", id="back", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back":
            self.app.pop_screen()
        else:
            self.dismiss(self._spec)
```

- [ ] **Step 3: Create dashboard.py**

```python
# loop_creator/wizard/dashboard.py
from __future__ import annotations
import threading
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ProgressBar, DataTable
from textual.binding import Binding
from loop_creator.spec import LoopSpec
from loop_creator.runner import run_loop
from loop_creator.gepa.engine import GenerationEvent


class DashboardApp(App):
    CSS = """
    #status { height: 3; background: $panel; padding: 0 1; }
    #variants { height: 1fr; }
    #progress-bar { dock: bottom; height: 3; }
    """
    TITLE = "loop-creator — running"
    BINDINGS = [
        Binding("q", "stop", "Stop"),
        Binding("p", "pause", "Pause"),
        Binding("b", "show_best", "Best"),
    ]

    def __init__(self, spec: LoopSpec, loop_dir: str):
        super().__init__()
        self._spec = spec
        self._loop_dir = loop_dir
        self._stopped = threading.Event()
        self._best_score = 0.0
        self._current_gen = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Loop: {self._spec.id} · Gen 0/{self._spec.gepa.max_generations} · Best: 0.00", id="status")
        yield DataTable(id="variants")
        yield ProgressBar(total=self._spec.gepa.max_generations, id="progress-bar")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#variants", DataTable)
        table.add_columns("Variant", "Score", "Reason")
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        def on_event(event: GenerationEvent):
            self.call_from_thread(self._update_ui, event)

        run_loop(self._spec, self._loop_dir, on_event=on_event)
        self.call_from_thread(self.exit)

    def _update_ui(self, event: GenerationEvent):
        self._current_gen = event.generation
        self._best_score = event.best_score
        status = self.query_one("#status", Static)
        status.update(
            f"Loop: {self._spec.id} · Gen {event.generation}/{self._spec.gepa.max_generations} "
            f"· Best: {event.best_score:.2f} {'↑' if event.event_type != 'done' else '✓'}"
        )
        table = self.query_one("#variants", DataTable)
        table.clear()
        for i, v in enumerate(event.variants[:5]):
            label = "★ " if v.score == event.best_score else f"{chr(65+i)} "
            table.add_row(label + v.prompt[:60], f"{v.score:.2f}", v.reason[:50])
        self.query_one("#progress-bar", ProgressBar).advance(1)

    def action_stop(self):
        self._stopped.set()
        self.exit()

    def action_show_best(self):
        import os
        best_path = os.path.join(self._loop_dir, "best.md")
        if os.path.isfile(best_path):
            self.notify(open(best_path).read()[:300], title="Best so far")
```

- [ ] **Step 4: Smoke test wizard imports**

```bash
python -c "from loop_creator.wizard.app import WizardApp; print('Wizard OK')"
python -c "from loop_creator.wizard.dashboard import DashboardApp; print('Dashboard OK')"
```

Expected: `Wizard OK` and `Dashboard OK` with no import errors.

- [ ] **Step 5: Commit**

```bash
git add loop_creator/wizard/ 
git commit -m "feat: add Textual wizard (7-step) and live dashboard"
```

---

### Task 13: README

**Files:**
- Create: `docs/README.md`

- [ ] **Step 1: Write README**

```markdown
# loop-creator

Build and run GEPA-powered evolutionary AI loops for any dev task — coding, debugging, documentation, RFC writing, design docs, prompt improvement, and more.

**No API keys required.** Works with Claude CLI, Devin CLI, and local Ollama.

## Install

```bash
pip install -e .
```

Prerequisites: Python 3.11+. At least one of:
- `claude` CLI (Claude Code) — already authenticated
- `devin` CLI — already authenticated  
- Ollama running locally (`ollama serve`)

## Quick Start

```bash
loop-creator new
```

The wizard walks you through 7 steps: loop type → task → goal → context → CLI selection → GEPA params → preview. Saves a YAML spec and optionally runs immediately.

## CLI Commands

| Command | Description |
|---------|-------------|
| `loop-creator new` | Launch the interactive wizard |
| `loop-creator run <spec.yaml>` | Run a loop from a YAML file |
| `loop-creator run <spec.yaml> --watch` | Run with live TUI dashboard |
| `loop-creator ls` | List all saved loops and their best scores |
| `loop-creator history <loop-id>` | Show generation-by-generation evolution |
| `loop-creator best <loop-id>` | Print the winning prompt and output |
| `loop-creator context <loop-id>` | Edit context for an existing loop |

## Loop Spec (YAML)

```yaml
id: fix-auth-bug
type: coding                          # coding|debugging|docs|rfc|design|prompt|custom
task: "Fix the JWT expiry bug"
goal: "All auth tests pass, no 401s"

generator:
  cli: ollama                         # claude|ollama|devin
  model: codellama                    # optional, defaults per CLI

judge:
  cli: claude
  rubric: ""                          # leave blank to use the loop type's default rubric

context:
  project: true                       # auto-scrape repo structure + key files
  history: true                       # inject prior iteration scores
  external:
    - docs/auth-design.md             # file paths or URLs
  mcp_auto_discover: true             # auto-detect MCP servers from ~/.claude/settings.json

gepa:
  population_size: 5                  # variants generated per generation
  top_k: 2                            # survivors passed to next generation
  max_generations: 10                 # hard cap
  fitness_threshold: 0.85             # halt when any variant reaches this score
  stagnation_limit: 3                 # halt after N generations with no improvement
  mutation_operators: [rephrase, expand, constrain, crossover]
```

## Loop Types

| Type | What the judge measures |
|------|------------------------|
| `coding` | Code correctness, test pass rate, cleanliness |
| `debugging` | Root cause identified, fix applied, no regression |
| `docs` | Completeness, accuracy, readability |
| `rfc` | Covers motivation, design, alternatives, trade-offs |
| `design` | Clear component boundaries, defined interfaces |
| `prompt` | Clarity, specificity, hallucination resistance, format, token efficiency |
| `custom` | You define the rubric entirely |

## GEPA Explained

GEPA runs an evolutionary search over prompt variants:

1. **Seed** — generates N variants of your task prompt
2. **Score** — the judge CLI scores each against your goal (0.0–1.0)
3. **Select** — top-K variants survive to the next generation
4. **Mutate** — four operators create new variants: `rephrase`, `expand`, `constrain`, `crossover`
5. **Repeat** — until fitness threshold, max generations, or stagnation limit is hit

The best output is saved to `.loop-creator/<loop-id>/best.md`.

**Tuning tips:**
- Lower `fitness_threshold` (e.g. 0.7) = faster, good for exploration
- Higher `population_size` = more diverse search, more CLI calls
- `stagnation_limit: 2` = exit early if stuck (good for tight deadlines)

## Context System

| Source | What it provides |
|--------|-----------------|
| `project: true` | Directory tree, key files, tech stack, recent git commits |
| `history: true` | Summary of top/bottom performers from prior runs |
| `external: [path]` | Files, URLs, or pasted text you attach |
| `mcp_auto_discover: true` | Any MCP servers found in `~/.claude/settings.json` |

The wizard auto-suggests relevant files based on your task description. You can toggle, edit, or add any source before launching.

## CLI Adapter Setup

Check which CLIs are available:

```bash
which claude    # Claude Code CLI
which devin     # Devin CLI
ollama list     # Ollama models
```

The wizard only shows available CLIs. If a spec names an unavailable CLI, the tool fails fast before wasting any generations.

### Adding a custom CLI adapter

Drop a Python file into `~/.loop-creator/adapters/` implementing:

```python
from loop_creator.adapters.base import LLMAdapter

class MyCLIAdapter(LLMAdapter):
    def call(self, system: str, user: str) -> str: ...
    def call_structured(self, system: str, user: str, schema: dict) -> dict: ...
    def is_available(self) -> bool: ...
```

The wizard picks it up automatically.

## Troubleshooting

**Scores consistently low (< 0.4):** The wizard will prompt you to refine your goal. Make it more measurable: "all tests pass" beats "looks good".

**Stagnation hits every run:** Try increasing `population_size` or adding more external context.

**Context budget exceeded:** Reduce external files or set `project: false` if the task doesn't need repo context.

**CLI not found:** Run `which <cli>` to verify it's on PATH. The wizard shows only available CLIs.

## Running Tests

```bash
pytest tests/ -v
```
```

- [ ] **Step 2: Verify README renders correctly**

```bash
# Check the file was created
ls docs/README.md
wc -l docs/README.md
```

Expected: file exists, 100+ lines.

- [ ] **Step 3: Run full test suite**

```bash
cd /Users/avinashvundyala/Documents/github/skills
pytest tests/ -v
```

Expected: all tests PASS, no failures.

- [ ] **Step 4: Final commit**

```bash
git add docs/README.md
git commit -m "docs: add comprehensive README with usage guide, loop types, GEPA tuning, and troubleshooting"
```

---

## Self-Review

### Spec coverage check

| Spec requirement | Task |
|-----------------|------|
| CLI adapters: claude, devin, ollama | Task 2 |
| `is_available()` for auto-detection | Task 2 |
| Scorer (prompt loops) | Task 3 |
| Loop spec YAML with all fields | Task 4 |
| Judge module with score parsing | Task 5 |
| Mutation operators (4) | Task 6 |
| GEPA engine: population, stagnation, threshold | Task 7 |
| Context: project, history, external, MCP, bundle | Task 8 |
| Loop type registry (7 types) | Task 9 |
| Adapter factory + runner orchestration | Task 10 |
| Typer CLI (all 6 commands) | Task 11 |
| Textual wizard (7 steps) | Task 12 |
| Live dashboard | Task 12 |
| README | Task 13 |
| Portable YAML spec (any tool can execute) | Task 4 + Task 10 |
| `loops/` dir for saved specs | Task 1 |
| `.loop-creator/<id>/best.md` output | Task 10 |
| `.loop-creator/<id>/history.jsonl` | Task 8 + Task 10 |

All spec requirements covered. ✓

### Type consistency check

- `LLMAdapter` used consistently across Tasks 2, 3, 5, 6, 7, 10 ✓
- `GenerationEvent.variants: list[Variant]` and `Variant.score: float` consistent across Tasks 7, 12 ✓
- `LoopSpec` passed through runner → CLI → wizard consistently ✓
- `Judge.score(output, rubric) -> tuple[float, str]` matches usage in engine ✓
- `build_adapter(cli, model) -> LLMAdapter` matches usage in runner ✓
