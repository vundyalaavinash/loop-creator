# Loop Creator SP2 — macOS Tauri App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bundled macOS Tauri 2.x desktop app that wraps the SP1 `loop-creator` Python package with a Warp-themed GUI for creating, editing, and monitoring GEPA dev loops.

**Architecture:** A PyInstaller-bundled FastAPI server (`lc_server`) runs as a Tauri sidecar on a random port; the Tauri Rust core spawns it on launch, injects the port as `window.__LC_PORT__`, and kills it on exit; the React 18 webview (Vite + Tailwind Warp theme + Monaco) talks to it via REST + SSE streaming.

**Tech Stack:** Tauri 2.x (Rust), React 18 + TypeScript + Tailwind 3 + Vite 5, FastAPI + uvicorn (Python 3.11+), PyInstaller 6, @monaco-editor/react 4, react-router-dom v6, Vitest + React Testing Library, pytest + httpx

## Global Constraints

- All SP2 code lives under `tauri-app/` at the project root (`/Users/avinashvundyala/Documents/github/skills/`)
- Server Python package is named `lc_server` (NOT `loop_creator`) to avoid shadowing SP1's installed package
- SP1 (`loop_creator`) is always imported from the installed package — never duplicate SP1 code
- Loop storage in Tauri app: `~/.loop-creator/<id>/spec.yaml` and `~/.loop-creator/<id>/` for state (history.jsonl, best.md)
- Warp theme exact colours: bg-base `#1C1C1C`, bg-surface `#242424`, bg-elevated `#2E2E2E`, accent-teal `#01C7B1`, accent-purple `#9B6DFF`, text-primary `#F0F0F0`, text-muted `#8A8A8A`, border-color `#383838`
- Fonts: JetBrains Mono (code/mono), Inter (UI labels) — both via `@fontsource/`
- Rounded corners: panels `rounded-lg` (8px), inputs `rounded` (4px). No drop shadows.
- SSE format: `data: <JSON>\n\n` via `StreamingResponse(media_type="text/event-stream")`
- `run_loop` runs in a background thread; events bridged to async via `loop.call_soon_threadsafe`
- Python tests: pytest with `TestClient` from `fastapi.testclient`, `tmp_path` + `monkeypatch` for isolation
- React tests: Vitest + React Testing Library, jsdom environment, globals: true
- Tauri version: 2.x; React 18.x; Vite 5.x; Tailwind 3.x
- SP1 patch required: add `project_root: str = ""` to `ContextSpec` in `loop_creator/spec.py` and use it in `loop_creator/runner.py`

---

### Task 1: SP1 patch + lc_server scaffold + health endpoint

**Files:**
- Modify: `loop_creator/spec.py` — add `project_root` field to ContextSpec
- Modify: `loop_creator/runner.py` — use `project_root` when scraping project context
- Create: `tauri-app/lc_server/__init__.py`
- Create: `tauri-app/lc_server/main.py`
- Create: `tauri-app/pyproject.toml`
- Create: `tauri-app/tests/__init__.py`
- Create: `tauri-app/tests/server/__init__.py`
- Create: `tauri-app/tests/server/conftest.py`
- Create: `tauri-app/tests/server/test_health.py`

**Interfaces:**
- Produces: `create_app() -> FastAPI` (used by all later server tests and by main entrypoint)

- [ ] **Step 1: Patch ContextSpec to add project_root**

In `loop_creator/spec.py`, add `project_root: str = ""` to `ContextSpec`:

```python
class ContextSpec(BaseModel):
    project: bool = True
    history: bool = True
    external: list[str] = Field(default_factory=list)
    mcp_auto_discover: bool = True
    project_root: str = ""
```

- [ ] **Step 2: Patch runner.py to use project_root**

In `loop_creator/runner.py`, change the project context line:

```python
# Before:
if spec.context.project:
    ctx_parts["project"] = scrape_project(os.getcwd())

# After:
if spec.context.project:
    root = spec.context.project_root or os.getcwd()
    ctx_parts["project"] = scrape_project(root)
```

- [ ] **Step 3: Verify SP1 tests still pass**

```bash
cd /Users/avinashvundyala/Documents/github/skills
pytest tests/ -q
```
Expected: `54 passed`

- [ ] **Step 4: Write the failing health test**

Create `tauri-app/tests/server/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from lc_server.main import create_app
    return TestClient(create_app())

@pytest.fixture(autouse=True)
def isolate_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".loop-creator").mkdir()
```

Create `tauri-app/tests/server/test_health.py`:
```python
def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
```

- [ ] **Step 5: Run test to confirm it fails**

```bash
cd tauri-app
python -m pytest tests/server/test_health.py -v
```
Expected: `ImportError: No module named 'lc_server'`

- [ ] **Step 6: Create pyproject.toml**

Create `tauri-app/pyproject.toml`:
```toml
[project]
name = "lc-server"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:BuildBackend"
```

- [ ] **Step 7: Create lc_server scaffold**

Create `tauri-app/lc_server/__init__.py` (empty).

Create `tauri-app/lc_server/main.py`:
```python
from __future__ import annotations
import argparse
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="Loop Creator Server", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["tauri://localhost", "http://localhost:5173", "http://localhost:*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
```

- [ ] **Step 8: Install dependencies and run test**

```bash
cd tauri-app
pip install fastapi uvicorn pytest pytest-asyncio httpx
pip install -e ../    # install SP1
python -m pytest tests/server/test_health.py -v
```
Expected: `PASSED`

- [ ] **Step 9: Commit**

```bash
git add loop_creator/spec.py loop_creator/runner.py tauri-app/
git commit -m "feat(sp2): scaffold lc_server + patch SP1 ContextSpec with project_root"
```

---

### Task 2: Loops CRUD routes

**Files:**
- Create: `tauri-app/lc_server/routes/__init__.py`
- Create: `tauri-app/lc_server/routes/loops.py`
- Modify: `tauri-app/lc_server/main.py` — include loops router
- Create: `tauri-app/tests/server/test_loops_crud.py`

**Interfaces:**
- Consumes: `create_app()` from Task 1
- Produces: `POST /api/loops`, `GET /api/loops`, `GET /api/loops/{id}`, `DELETE /api/loops/{id}`

- [ ] **Step 1: Write failing tests**

Create `tauri-app/tests/server/test_loops_crud.py`:
```python
import json
import yaml
import pytest
from pathlib import Path


def _make_loop(tmp_path, loop_id="myloop"):
    d = tmp_path / ".loop-creator" / loop_id
    d.mkdir(parents=True, exist_ok=True)
    spec = {
        "id": loop_id, "type": "coding", "task": "write tests",
        "goal": "100% coverage",
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    (d / "spec.yaml").write_text(yaml.dump(spec))
    return d


def test_create_loop(client, tmp_path):
    payload = {
        "id": "newloop", "type": "coding", "task": "do stuff", "goal": "do it well",
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    r = client.post("/api/loops", json=payload)
    assert r.status_code == 200
    assert r.json()["id"] == "newloop"
    loop_dir = tmp_path / ".loop-creator" / "newloop"
    assert (loop_dir / "spec.yaml").exists()


def test_list_loops_returns_saved(client, tmp_path):
    _make_loop(tmp_path, "alpha")
    _make_loop(tmp_path, "beta")
    r = client.get("/api/loops")
    assert r.status_code == 200
    ids = [l["id"] for l in r.json()]
    assert "alpha" in ids
    assert "beta" in ids


def test_get_loop(client, tmp_path):
    _make_loop(tmp_path, "getme")
    r = client.get("/api/loops/getme")
    assert r.status_code == 200
    assert r.json()["id"] == "getme"


def test_delete_loop(client, tmp_path):
    _make_loop(tmp_path, "deleteme")
    r = client.delete("/api/loops/deleteme")
    assert r.status_code == 200
    assert not (tmp_path / ".loop-creator" / "deleteme").exists()
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app && python -m pytest tests/server/test_loops_crud.py -v
```
Expected: `404 Not Found` errors (routes don't exist yet)

- [ ] **Step 3: Implement loops CRUD routes**

Create `tauri-app/lc_server/routes/__init__.py` (empty).

Create `tauri-app/lc_server/routes/loops.py`:
```python
from __future__ import annotations
import json
import shutil
import threading
import time
from dataclasses import asdict
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from loop_creator.spec import LoopSpec, load_spec, save_spec

router = APIRouter(prefix="/api/loops")


def _loop_dir(loop_id: str) -> Path:
    return Path.home() / ".loop-creator" / loop_id


@router.post("")
def create_loop(spec: LoopSpec):
    loop_dir = _loop_dir(spec.id)
    loop_dir.mkdir(parents=True, exist_ok=True)
    save_spec(spec, str(loop_dir / "spec.yaml"))
    return {"id": spec.id, "status": "created"}


@router.get("")
def list_loops():
    base = Path.home() / ".loop-creator"
    if not base.exists():
        return []
    result = []
    for d in sorted(base.iterdir()):
        spec_path = d / "spec.yaml"
        if not spec_path.exists():
            continue
        try:
            spec = load_spec(str(spec_path))
            loop_type = spec.type
        except Exception:
            loop_type = "unknown"
        history_path = d / "history.jsonl"
        last_modified = history_path.stat().st_mtime if history_path.exists() else 0
        active = (time.time() - last_modified) < 60
        best_score = None
        if history_path.exists():
            lines = [l for l in history_path.read_text().splitlines() if l.strip()]
            scores = [json.loads(l).get("score", 0) for l in lines]
            best_score = max(scores) if scores else None
        result.append({
            "id": d.name,
            "name": d.name,
            "loop_type": loop_type,
            "last_modified": last_modified,
            "best_score": best_score,
            "active": active,
        })
    return result


@router.get("/{loop_id}")
def get_loop(loop_id: str):
    spec_path = _loop_dir(loop_id) / "spec.yaml"
    if not spec_path.exists():
        raise HTTPException(404, "Loop not found")
    spec = load_spec(str(spec_path))
    return spec.model_dump()


@router.delete("/{loop_id}")
def delete_loop(loop_id: str):
    d = _loop_dir(loop_id)
    if not d.exists():
        raise HTTPException(404, "Loop not found")
    shutil.rmtree(d)
    return {"id": loop_id, "status": "deleted"}
```

- [ ] **Step 4: Register router in main.py**

```python
# In lc_server/main.py, add after imports:
from lc_server.routes import loops as loops_routes

# In create_app(), before return:
    app.include_router(loops_routes.router)
```

- [ ] **Step 5: Run tests**

```bash
cd tauri-app && python -m pytest tests/server/test_loops_crud.py -v
```
Expected: `4 passed`

- [ ] **Step 6: Commit**

```bash
git add tauri-app/
git commit -m "feat(sp2): add loops CRUD routes (create, list, get, delete)"
```

---

### Task 3: Loops run (SSE) + history + best routes

**Files:**
- Modify: `tauri-app/lc_server/routes/loops.py` — add run, history, best endpoints
- Create: `tauri-app/tests/server/test_loops_run.py`

**Interfaces:**
- Consumes: `run_loop` from `loop_creator.runner`, `GenerationEvent`/`Variant` from `loop_creator.gepa.engine`
- Produces: `POST /api/loops/{id}/run` (SSE), `GET /api/loops/{id}/history`, `GET /api/loops/{id}/best`

- [ ] **Step 1: Write failing tests**

Create `tauri-app/tests/server/test_loops_run.py`:
```python
import yaml
import pytest
from unittest.mock import patch
from pathlib import Path
from loop_creator.gepa.engine import GenerationEvent, Variant


def _fake_variant():
    return Variant(prompt="p", output="o", score=0.9, reason="great", generation=1)


def _fake_run_loop(spec, loop_dir, on_event=None):
    v = _fake_variant()
    ev = GenerationEvent(generation=1, variants=[v], best_score=0.9)
    done = GenerationEvent(generation=1, variants=[v], best_score=0.9, event_type="done")
    if on_event:
        on_event(ev)
        on_event(done)
    return v


def _make_loop(tmp_path, loop_id="runme"):
    d = tmp_path / ".loop-creator" / loop_id
    d.mkdir(parents=True, exist_ok=True)
    spec = {
        "id": loop_id, "type": "coding", "task": "t", "goal": "g",
        "generator": {"cli": "claude", "model": ""},
        "judge": {"cli": "claude", "rubric": "", "model": ""},
    }
    (d / "spec.yaml").write_text(yaml.dump(spec))
    return d


def test_run_streams_event_data(client, tmp_path):
    d = _make_loop(tmp_path)
    with patch("lc_server.routes.loops.run_loop", _fake_run_loop):
        r = client.post("/api/loops/runme/run")
    assert "text/event-stream" in r.headers["content-type"]
    assert "data: " in r.text
    assert "generation" in r.text


def test_run_returns_404_for_missing_loop(client):
    r = client.post("/api/loops/ghost/run")
    assert r.status_code == 404


def test_history_returns_jsonl_as_array(client, tmp_path):
    d = _make_loop(tmp_path, "histloop")
    import json
    (d / "history.jsonl").write_text(
        json.dumps({"generation": 1, "score": 0.8, "prompt": "p", "reason": "r"}) + "\n"
    )
    r = client.get("/api/loops/histloop/history")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert data[0]["score"] == 0.8


def test_best_returns_markdown(client, tmp_path):
    d = _make_loop(tmp_path, "bestloop")
    (d / "best.md").write_text("# Best Result\n\nScore: 0.9\n")
    r = client.get("/api/loops/bestloop/best")
    assert r.status_code == 200
    assert r.json()["content"].startswith("# Best Result")
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app && python -m pytest tests/server/test_loops_run.py -v
```
Expected: `404` errors

- [ ] **Step 3: Implement run, history, best endpoints**

Add to `tauri-app/lc_server/routes/loops.py` (after the existing imports and endpoints):

```python
import asyncio
from loop_creator.runner import run_loop


@router.post("/{loop_id}/run")
async def run_loop_sse(loop_id: str):
    loop_dir = _loop_dir(loop_id)
    if not (loop_dir / "spec.yaml").exists():
        raise HTTPException(404, "Loop not found")
    spec = load_spec(str(loop_dir / "spec.yaml"))

    main_loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def run_in_thread():
        def on_event(ev):
            main_loop.call_soon_threadsafe(queue.put_nowait, ev)
        try:
            run_loop(spec, str(loop_dir), on_event=on_event)
        finally:
            main_loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=run_in_thread, daemon=True).start()

    async def generate():
        while True:
            ev = await queue.get()
            if ev is None:
                break
            yield f"data: {json.dumps(asdict(ev))}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/{loop_id}/history")
def get_history(loop_id: str):
    history_path = _loop_dir(loop_id) / "history.jsonl"
    if not history_path.exists():
        return []
    lines = [l for l in history_path.read_text().splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


@router.get("/{loop_id}/best")
def get_best(loop_id: str):
    best_path = _loop_dir(loop_id) / "best.md"
    if not best_path.exists():
        raise HTTPException(404, "No best result yet")
    return {"content": best_path.read_text()}
```

- [ ] **Step 4: Run tests**

```bash
cd tauri-app && python -m pytest tests/server/test_loops_run.py -v
```
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add tauri-app/
git commit -m "feat(sp2): add loops run SSE, history, and best endpoints"
```

---

### Task 4: Files + context routes

**Files:**
- Create: `tauri-app/lc_server/routes/files.py`
- Create: `tauri-app/lc_server/routes/context.py`
- Modify: `tauri-app/lc_server/main.py` — include both routers
- Create: `tauri-app/tests/server/test_files.py`
- Create: `tauri-app/tests/server/test_context.py`

**Interfaces:**
- Produces: `GET /api/files`, `GET /api/files/content`, `PUT /api/files/content`, `GET /api/context/project`, `GET /api/context/mcp`

- [ ] **Step 1: Write failing tests**

Create `tauri-app/tests/server/test_files.py`:
```python
def test_list_files(client, tmp_path):
    (tmp_path / "foo.py").write_text("x = 1")
    (tmp_path / "bar.md").write_text("# hi")
    r = client.get(f"/api/files?path={tmp_path}")
    assert r.status_code == 200
    names = [f["name"] for f in r.json()]
    assert "foo.py" in names
    assert "bar.md" in names


def test_read_file(client, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    r = client.get(f"/api/files/content?path={f}")
    assert r.status_code == 200
    assert r.json()["content"] == "hello world"


def test_write_file(client, tmp_path):
    f = tmp_path / "out.txt"
    r = client.put("/api/files/content", json={"path": str(f), "content": "written"})
    assert r.status_code == 200
    assert f.read_text() == "written"
```

Create `tauri-app/tests/server/test_context.py`:
```python
from unittest.mock import patch


def test_project_context(client, tmp_path):
    with patch("lc_server.routes.context.scrape_project", return_value="## tree"):
        r = client.get(f"/api/context/project?path={tmp_path}")
    assert r.status_code == 200
    assert r.json()["context"] == "## tree"


def test_mcp_servers(client):
    with patch("lc_server.routes.context.discover_mcp_servers", return_value=["github", "slack"]):
        r = client.get("/api/context/mcp")
    assert r.status_code == 200
    assert r.json() == ["github", "slack"]
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd tauri-app && python -m pytest tests/server/test_files.py tests/server/test_context.py -v
```
Expected: `404` / import errors

- [ ] **Step 3: Implement files route**

Create `tauri-app/lc_server/routes/files.py`:
```python
from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/files")


class WriteBody(BaseModel):
    path: str
    content: str


@router.get("")
def list_files(path: str):
    p = Path(path)
    if not p.is_dir():
        raise HTTPException(400, "Not a directory")
    nodes = []
    for child in sorted(p.iterdir()):
        if child.name.startswith("."):
            continue
        nodes.append({
            "name": child.name,
            "path": str(child),
            "is_dir": child.is_dir(),
        })
    return nodes


@router.get("/content")
def read_file(path: str):
    p = Path(path)
    if not p.is_file():
        raise HTTPException(404, "File not found")
    try:
        return {"path": path, "content": p.read_text(encoding="utf-8")}
    except UnicodeDecodeError:
        raise HTTPException(400, "File is not UTF-8 text")


@router.put("/content")
def write_file(body: WriteBody):
    p = Path(body.path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body.content, encoding="utf-8")
    return {"path": body.path, "status": "written"}
```

- [ ] **Step 4: Implement context route**

Create `tauri-app/lc_server/routes/context.py`:
```python
from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter
from loop_creator.context.project import scrape_project
from loop_creator.context.mcp import discover_mcp_servers

router = APIRouter(prefix="/api/context")


@router.get("/project")
def get_project_context(path: str = "."):
    context = scrape_project(path)
    return {"context": context}


@router.get("/mcp")
def get_mcp_servers():
    return discover_mcp_servers()
```

- [ ] **Step 5: Register routers in main.py**

```python
# Add imports in lc_server/main.py:
from lc_server.routes import loops as loops_routes
from lc_server.routes import files as files_routes
from lc_server.routes import context as context_routes

# In create_app():
    app.include_router(loops_routes.router)
    app.include_router(files_routes.router)
    app.include_router(context_routes.router)
```

- [ ] **Step 6: Run all server tests**

```bash
cd tauri-app && python -m pytest tests/server/ -v
```
Expected: `12 passed`

- [ ] **Step 7: Commit**

```bash
git add tauri-app/
git commit -m "feat(sp2): add files and context API routes"
```

---

### Task 5: PyInstaller spec + build script

**Files:**
- Create: `tauri-app/loop_creator_server.spec`
- Create: `tauri-app/scripts/build.sh`
- Create: `tauri-app/src-tauri/binaries/.gitkeep`

**Interfaces:**
- Produces: `dist/loop_creator_server` binary (bundled with lc_server + loop_creator + fastapi + uvicorn)

- [ ] **Step 1: Create PyInstaller spec**

Create `tauri-app/loop_creator_server.spec`:
```python
# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ["run_server.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "loop_creator",
        "loop_creator.adapters",
        "loop_creator.gepa",
        "loop_creator.context",
        "loop_creator.loop_types",
        "loop_creator.wizard",
        "tiktoken_ext",
        "tiktoken_ext.openai_public",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="loop_creator_server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
```

- [ ] **Step 2: Create server entrypoint**

Create `tauri-app/run_server.py`:
```python
from lc_server.main import app, create_app
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    uvicorn.run(create_app(), host="127.0.0.1", port=args.port, log_level="warning")
```

- [ ] **Step 3: Create build script**

Create `tauri-app/scripts/build.sh`:
```bash
#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

echo "→ Creating venv..."
python3 -m venv "$ROOT/.venv-build"
source "$ROOT/.venv-build/bin/activate"

echo "→ Installing dependencies..."
pip install --quiet -e "$ROOT/../"   # SP1 loop-creator
pip install --quiet fastapi uvicorn pyinstaller tiktoken pyyaml httpx rich textual typer

echo "→ Running PyInstaller..."
cd "$ROOT"
pyinstaller loop_creator_server.spec --distpath dist --workpath build-tmp --noconfirm

echo "→ Copying binary to src-tauri/binaries/..."
ARCH=$(python3 -c "import platform; m = platform.machine(); print('aarch64' if m == 'arm64' else m)")
DEST="$ROOT/src-tauri/binaries/loop_creator_server-${ARCH}-apple-darwin"
cp "$ROOT/dist/loop_creator_server" "$DEST"
chmod +x "$DEST"

echo "✓ Built: $DEST"
deactivate
```

- [ ] **Step 4: Create binaries placeholder**

```bash
mkdir -p tauri-app/src-tauri/binaries
touch tauri-app/src-tauri/binaries/.gitkeep
```

- [ ] **Step 5: Verify build script syntax**

```bash
bash -n tauri-app/scripts/build.sh
```
Expected: no output (syntax OK)

- [ ] **Step 6: Commit**

```bash
git add tauri-app/loop_creator_server.spec tauri-app/run_server.py tauri-app/scripts/ tauri-app/src-tauri/binaries/.gitkeep
git commit -m "feat(sp2): add PyInstaller spec and build script"
```

---

### Task 6: Tauri Rust scaffold + sidecar lifecycle

**Files:**
- Create: `tauri-app/src-tauri/Cargo.toml`
- Create: `tauri-app/src-tauri/build.rs`
- Create: `tauri-app/src-tauri/tauri.conf.json`
- Create: `tauri-app/src-tauri/capabilities/default.json`
- Create: `tauri-app/src-tauri/src/main.rs`

**Interfaces:**
- Produces: macOS `.app` bundle that starts `loop_creator_server` sidecar and injects port into webview

- [ ] **Step 1: Create Cargo.toml**

Create `tauri-app/src-tauri/Cargo.toml`:
```toml
[package]
name = "loop-creator-app"
version = "0.1.0"
edition = "2021"
rust-version = "1.77"

[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = ["macos-private-api"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

- [ ] **Step 2: Create build.rs**

Create `tauri-app/src-tauri/build.rs`:
```rust
fn main() {
    tauri_build::build()
}
```

- [ ] **Step 3: Create tauri.conf.json**

Create `tauri-app/src-tauri/tauri.conf.json`:
```json
{
  "productName": "Loop Creator",
  "version": "0.1.0",
  "identifier": "dev.loop-creator.app",
  "build": {
    "frontendDist": "../web/dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "cd ../web && npm run dev",
    "beforeBuildCommand": "cd ../web && npm run build"
  },
  "app": {
    "withGlobalTauri": false,
    "windows": [
      {
        "title": "Loop Creator",
        "width": 1280,
        "height": 840,
        "visible": false
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "dmg",
    "externalBin": ["binaries/loop_creator_server"],
    "icon": [],
    "macOS": {
      "entitlements": null,
      "exceptionDomain": "",
      "frameworks": [],
      "signingIdentity": null
    }
  }
}
```

- [ ] **Step 4: Create capabilities**

Create `tauri-app/src-tauri/capabilities/default.json`:
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "core:window:allow-start-dragging",
    "core:window:allow-set-focus"
  ]
}
```

- [ ] **Step 5: Create main.rs**

Create `tauri-app/src-tauri/src/main.rs`:
```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::net::TcpListener;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::{Duration, Instant};

struct SidecarState(Mutex<Option<Child>>);

fn find_free_port() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind port 0");
    listener.local_addr().unwrap().port()
}

fn wait_for_server(port: u16, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if TcpListener::bind(format!("127.0.0.1:{}", port)).is_err() {
            // Port is in use — server is up
            std::thread::sleep(Duration::from_millis(200));
            return true;
        }
        std::thread::sleep(Duration::from_millis(400));
    }
    false
}

fn main() {
    tauri::Builder::default()
        .manage(SidecarState(Mutex::new(None)))
        .setup(|app| {
            let port = find_free_port();

            // Locate sidecar next to our own executable
            let exe_dir = std::env::current_exe()
                .unwrap()
                .parent()
                .unwrap()
                .to_path_buf();
            let sidecar = exe_dir.join("loop_creator_server");

            let child = Command::new(&sidecar)
                .arg("--port")
                .arg(port.to_string())
                .spawn()
                .unwrap_or_else(|e| panic!("Failed to start loop_creator_server: {e}"));

            *app.state::<SidecarState>().0.lock().unwrap() = Some(child);

            if !wait_for_server(port, Duration::from_secs(15)) {
                eprintln!("loop_creator_server did not start in time");
            }

            let window = app.get_webview_window("main").unwrap();
            window
                .eval(&format!("window.__LC_PORT__ = {}", port))
                .unwrap();
            window.show().unwrap();

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(mut child) =
                    app.state::<SidecarState>().0.lock().unwrap().take()
                {
                    let _ = child.kill();
                }
            }
        });
}
```

- [ ] **Step 6: Verify Rust compiles**

```bash
cd tauri-app/src-tauri
cargo build 2>&1 | tail -5
```
Expected: `Finished dev [unoptimized + debuginfo]` (may take 2–5 min first run)

- [ ] **Step 7: Commit**

```bash
git add tauri-app/src-tauri/
git commit -m "feat(sp2): Tauri Rust scaffold with sidecar spawn and port injection"
```

---

### Task 7: React scaffold + Warp theme + re-themed MVP components

**Files:**
- Create: `tauri-app/web/package.json`
- Create: `tauri-app/web/tailwind.config.js`
- Create: `tauri-app/web/vite.config.ts`
- Create: `tauri-app/web/index.html`
- Create: `tauri-app/web/src/main.tsx`
- Create: `tauri-app/web/src/index.css`
- Create: `tauri-app/web/src/setupTests.ts`
- Create: `tauri-app/web/src/components/ScoreBar.tsx`
- Create: `tauri-app/web/src/components/EvolutionViewer.tsx`
- Create: `tauri-app/web/src/components/ResultsPanel.tsx`
- Create: `tauri-app/web/src/components/__tests__/ScoreBar.test.tsx`

**Interfaces:**
- Produces: `ScoreBar`, `EvolutionViewer`, `ResultsPanel` components (Warp-themed, adapted to SP1 `Variant` type)

- [ ] **Step 1: Write the failing ScoreBar test**

Create `tauri-app/web/src/components/__tests__/ScoreBar.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { ScoreBar } from "../ScoreBar";

test("renders label and score percentage", () => {
  render(<ScoreBar label="Quality" score={0.75} />);
  expect(screen.getByText("Quality")).toBeInTheDocument();
  expect(screen.getByText("75%")).toBeInTheDocument();
});

test("renders teal bar with correct width", () => {
  const { container } = render(<ScoreBar label="Quality" score={0.5} />);
  const bar = container.querySelector(".bg-accent-teal");
  expect(bar).toHaveStyle({ width: "50%" });
});
```

- [ ] **Step 2: Create package.json and install**

Create `tauri-app/web/package.json`:
```json
{
  "name": "loop-creator-web",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@fontsource/inter": "^5.0.0",
    "@fontsource/jetbrains-mono": "^5.0.0",
    "@monaco-editor/react": "^4.6.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "jsdom": "^25.0.0",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3",
    "vite": "^5.4.10",
    "vitest": "^2.1.0"
  }
}
```

```bash
cd tauri-app/web && npm install
```

- [ ] **Step 3: Create Tailwind config with Warp theme**

Create `tauri-app/web/tailwind.config.js`:
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#1C1C1C",
        surface: "#242424",
        elevated: "#2E2E2E",
        "accent-teal": "#01C7B1",
        "accent-purple": "#9B6DFF",
        primary: "#F0F0F0",
        muted: "#8A8A8A",
        "border-color": "#383838",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
```

Create `tauri-app/web/postcss.config.js`:
```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
```

- [ ] **Step 4: Create Vite config**

Create `tauri-app/web/vite.config.ts`:
```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
  },
  server: { port: 5173 },
});
```

- [ ] **Step 5: Create index.html and entry files**

Create `tauri-app/web/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Loop Creator</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `tauri-app/web/src/index.css`:
```css
@import "@fontsource/inter";
@import "@fontsource/jetbrains-mono";
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  background-color: #1c1c1c;
  color: #f0f0f0;
  font-family: "Inter", sans-serif;
  margin: 0;
}
```

Create `tauri-app/web/src/setupTests.ts`:
```ts
import "@testing-library/jest-dom";
```

Create `tauri-app/web/src/main.tsx`:
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <div className="bg-base min-h-screen text-primary font-sans">
      <p className="p-8 text-accent-teal font-mono">Loop Creator loading...</p>
    </div>
  </React.StrictMode>
);
```

Create `tauri-app/web/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "types": ["vitest/globals"]
  },
  "include": ["src"]
}
```

- [ ] **Step 6: Create re-themed components**

Create `tauri-app/web/src/components/ScoreBar.tsx`:
```tsx
interface ScoreBarProps {
  label: string;
  score: number;        // 0.0 – 1.0
  prevScore?: number;
}

export function ScoreBar({ label, score, prevScore }: ScoreBarProps) {
  const pct = Math.round(score * 100);
  const delta = prevScore !== undefined ? Math.round((score - prevScore) * 100) : null;
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-muted font-mono">{label}</span>
        <span className="font-mono text-primary">
          {pct}%
          {delta !== null && (
            <span className={delta >= 0 ? "text-accent-teal ml-1" : "text-red-400 ml-1"}>
              {delta >= 0 ? `+${delta}` : delta}
            </span>
          )}
        </span>
      </div>
      <div className="h-1.5 bg-elevated rounded-full overflow-hidden">
        <div
          className="h-full bg-accent-teal transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
```

Create `tauri-app/web/src/components/EvolutionViewer.tsx`:
```tsx
import { GenerationEvent } from "../types";
import { ScoreBar } from "./ScoreBar";

interface Props {
  events: GenerationEvent[];
  isRunning: boolean;
}

export function EvolutionViewer({ events, isRunning }: Props) {
  const genEvents = events.filter((e) => e.event_type === "generation");
  if (genEvents.length === 0 && !isRunning) return null;

  return (
    <div className="bg-surface rounded-lg border border-border-color p-5">
      <h2 className="text-primary font-sans font-semibold text-base mb-4">
        Evolution Progress
        {isRunning && (
          <span className="ml-2 text-sm text-accent-teal animate-pulse font-mono">
            · running
          </span>
        )}
      </h2>
      <div className="space-y-3">
        {genEvents.map((ev) => {
          const top = ev.variants[0];
          const prev = genEvents[genEvents.indexOf(ev) - 1]?.variants[0];
          return (
            <div
              key={ev.generation}
              className="border border-border-color rounded bg-elevated p-3"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-muted">
                  Gen {ev.generation}
                </span>
                <span className="text-xs font-mono text-accent-teal">
                  best: {top ? (top.score * 100).toFixed(0) : "—"}%
                </span>
              </div>
              {top && (
                <>
                  <ScoreBar
                    label="score"
                    score={top.score}
                    prevScore={prev?.score}
                  />
                  <p className="text-xs text-muted font-mono mt-2 italic leading-relaxed">
                    {top.reason}
                  </p>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

Create `tauri-app/web/src/components/ResultsPanel.tsx`:
```tsx
import { Variant } from "../types";
import { ScoreBar } from "./ScoreBar";

interface Props {
  bestVariant: Variant | null;
}

export function ResultsPanel({ bestVariant }: Props) {
  if (!bestVariant) return null;

  return (
    <div className="bg-surface rounded-lg border border-border-color p-5">
      <h2 className="text-primary font-sans font-semibold text-base mb-4">
        Best Result
      </h2>
      <div className="mb-3">
        <ScoreBar label="score" score={bestVariant.score} />
      </div>
      <p className="text-xs text-muted font-mono mb-3 italic">
        {bestVariant.reason}
      </p>
      <div className="bg-elevated rounded border border-border-color p-3 mb-3">
        <p className="text-xs text-muted mb-1 font-mono">Output</p>
        <pre className="text-sm text-primary font-mono whitespace-pre-wrap leading-relaxed">
          {bestVariant.output}
        </pre>
      </div>
      <button
        onClick={() => navigator.clipboard.writeText(bestVariant.prompt)}
        className="text-xs font-mono text-accent-teal border border-accent-teal rounded px-3 py-1 hover:bg-accent-teal hover:text-base transition-colors"
      >
        Copy prompt
      </button>
    </div>
  );
}
```

- [ ] **Step 7: Run failing test, then verify it passes**

```bash
cd tauri-app/web && npx vitest run src/components/__tests__/ScoreBar.test.tsx
```
Expected: `2 passed`

- [ ] **Step 8: Commit**

```bash
git add tauri-app/web/
git commit -m "feat(sp2): React scaffold with Warp theme and re-themed MVP components"
```

---

### Task 8: types.ts + useLoop + useFiles hooks

**Files:**
- Create: `tauri-app/web/src/types.ts`
- Create: `tauri-app/web/src/hooks/useLoop.ts`
- Create: `tauri-app/web/src/hooks/useFiles.ts`
- Create: `tauri-app/web/src/hooks/__tests__/useFiles.test.ts`

**Interfaces:**
- Produces: `GenerationEvent`, `Variant`, `LoopSummary`, `FileNode`, `LoopSpec` types; `useLoop()`, `useFiles()` hooks

- [ ] **Step 1: Write failing hook test**

Create `tauri-app/web/src/hooks/__tests__/useFiles.test.ts`:
```ts
import { renderHook, act } from "@testing-library/react";
import { useFiles } from "../useFiles";

const PORT = 5001;
(window as any).__LC_PORT__ = PORT;

test("listFiles fetches and returns file nodes", async () => {
  const nodes = [{ name: "a.py", path: "/p/a.py", is_dir: false }];
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => nodes,
  } as any);

  const { result } = renderHook(() => useFiles());
  await act(async () => {
    await result.current.listFiles("/p");
  });

  expect(result.current.files).toEqual(nodes);
  expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/files?path=%2Fp")
  );
});
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/hooks/__tests__/useFiles.test.ts
```
Expected: `Cannot find module '../useFiles'`

- [ ] **Step 3: Create types.ts**

Create `tauri-app/web/src/types.ts`:
```ts
export interface Variant {
  prompt: string;
  output: string;
  score: number;       // 0.0 – 1.0
  reason: string;
  generation: number;
}

export interface GenerationEvent {
  event_type: "generation" | "done" | "error";
  generation: number;
  variants: Variant[];
  best_score: number;
}

export interface LoopSummary {
  id: string;
  name: string;
  loop_type: string;
  last_modified: number;   // epoch seconds
  best_score: number | null;
  active: boolean;
}

export interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  children?: FileNode[];
}

export interface LoopSpec {
  id: string;
  type: string;
  task: string;
  goal: string;
  generator: { cli: string; model: string };
  judge: { cli: string; rubric: string; model: string };
  context: {
    project: boolean;
    history: boolean;
    external: string[];
    mcp_auto_discover: boolean;
    project_root: string;
  };
  gepa: {
    population_size: number;
    top_k: number;
    max_generations: number;
    fitness_threshold: number;
    stagnation_limit: number;
  };
}

export function getBaseUrl(): string {
  const port = (window as any).__LC_PORT__ ?? 5001;
  return `http://localhost:${port}`;
}
```

- [ ] **Step 4: Create useLoop hook**

Create `tauri-app/web/src/hooks/useLoop.ts`:
```ts
import { useState, useCallback, useRef } from "react";
import { GenerationEvent, Variant, getBaseUrl } from "../types";

export function useLoop() {
  const [events, setEvents] = useState<GenerationEvent[]>([]);
  const [bestVariant, setBestVariant] = useState<Variant | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(async (loopId: string) => {
    setEvents([]);
    setBestVariant(null);
    setError(null);
    setIsRunning(true);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const response = await fetch(`${getBaseUrl()}/api/loops/${loopId}/run`, {
        method: "POST",
        signal: ctrl.signal,
      });
      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        for (const line of text.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const ev: GenerationEvent = JSON.parse(line.slice(6));
          setEvents((prev) => [...prev, ev]);
          if (ev.event_type === "done" && ev.variants.length > 0) {
            setBestVariant(ev.variants[0]);
          }
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        setError(e instanceof Error ? e.message : "Unknown error");
      }
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

- [ ] **Step 5: Create useFiles hook**

Create `tauri-app/web/src/hooks/useFiles.ts`:
```ts
import { useState, useCallback } from "react";
import { FileNode, getBaseUrl } from "../types";

export function useFiles() {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [content, setContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const listFiles = useCallback(async (path: string) => {
    const r = await fetch(
      `${getBaseUrl()}/api/files?path=${encodeURIComponent(path)}`
    );
    const data: FileNode[] = await r.json();
    setFiles(data);
    return data;
  }, []);

  const readFile = useCallback(async (path: string) => {
    const r = await fetch(
      `${getBaseUrl()}/api/files/content?path=${encodeURIComponent(path)}`
    );
    const data = await r.json();
    setContent(data.content);
    return data.content as string;
  }, []);

  const writeFile = useCallback(async (path: string, text: string) => {
    setError(null);
    const r = await fetch(`${getBaseUrl()}/api/files/content`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, content: text }),
    });
    if (!r.ok) setError("Save failed");
    return r.ok;
  }, []);

  return { files, content, error, listFiles, readFile, writeFile, setContent };
}
```

- [ ] **Step 6: Run test**

```bash
cd tauri-app/web && npx vitest run src/hooks/__tests__/useFiles.test.ts
```
Expected: `1 passed`

- [ ] **Step 7: Commit**

```bash
git add tauri-app/web/src/types.ts tauri-app/web/src/hooks/
git commit -m "feat(sp2): add types.ts and useLoop/useFiles hooks"
```

---

### Task 9: Sidebar + App router

**Files:**
- Create: `tauri-app/web/src/components/Sidebar.tsx`
- Create: `tauri-app/web/src/App.tsx`
- Create: `tauri-app/web/src/components/__tests__/Sidebar.test.tsx`

**Interfaces:**
- Produces: `<Sidebar />` nav component, `<App />` with react-router routes (placeholders for pages)

- [ ] **Step 1: Write failing Sidebar test**

Create `tauri-app/web/src/components/__tests__/Sidebar.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Sidebar } from "../Sidebar";

test("renders all nav items", () => {
  render(
    <MemoryRouter>
      <Sidebar />
    </MemoryRouter>
  );
  expect(screen.getByText("Loops")).toBeInTheDocument();
  expect(screen.getByText("New Loop")).toBeInTheDocument();
  expect(screen.getByText("Files")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/components/__tests__/Sidebar.test.tsx
```
Expected: `Cannot find module '../Sidebar'`

- [ ] **Step 3: Create Sidebar**

Create `tauri-app/web/src/components/Sidebar.tsx`:
```tsx
import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/loops", label: "Loops", icon: "⟳" },
  { to: "/new", label: "New Loop", icon: "+" },
  { to: "/files", label: "Files", icon: "◫" },
];

export function Sidebar() {
  return (
    <aside className="w-52 bg-surface border-r border-border-color flex flex-col h-screen flex-shrink-0">
      <div className="px-5 py-4 border-b border-border-color">
        <span className="text-accent-teal font-mono text-sm font-semibold tracking-widest uppercase">
          Loop Creator
        </span>
      </div>
      <nav className="flex-1 py-3">
        {NAV.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-2 text-sm font-mono transition-colors ${
                isActive
                  ? "text-accent-teal bg-elevated border-l-2 border-accent-teal"
                  : "text-muted hover:text-primary hover:bg-elevated"
              }`
            }
          >
            <span className="text-base">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-3 border-t border-border-color">
        <span className="text-xs text-muted font-mono">SP2 v0.1.0</span>
      </div>
    </aside>
  );
}
```

- [ ] **Step 4: Create App.tsx with router**

Create `tauri-app/web/src/App.tsx`:
```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";

// Pages imported lazily — stubs until Tasks 10-13 implement them
const Placeholder = ({ name }: { name: string }) => (
  <div className="flex-1 p-8 text-muted font-mono">{name} — coming soon</div>
);

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-base overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/loops" replace />} />
            <Route path="/loops" element={<Placeholder name="LoopList" />} />
            <Route path="/loops/:id/run" element={<Placeholder name="Dashboard" />} />
            <Route path="/new" element={<Placeholder name="Builder" />} />
            <Route path="/edit/:id" element={<Placeholder name="Builder (edit)" />} />
            <Route path="/files" element={<Placeholder name="FileEditor" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
```

Update `tauri-app/web/src/main.tsx` to render App:
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 5: Run tests**

```bash
cd tauri-app/web && npx vitest run src/components/__tests__/Sidebar.test.tsx
```
Expected: `1 passed`

- [ ] **Step 6: Smoke-test dev server**

```bash
cd tauri-app/web && npm run dev &
# Open http://localhost:5173 — should see sidebar + "LoopList — coming soon"
# Ctrl-C to stop
```

- [ ] **Step 7: Commit**

```bash
git add tauri-app/web/src/
git commit -m "feat(sp2): Sidebar nav and App router scaffold"
```

---

### Task 10: LoopList page

**Files:**
- Create: `tauri-app/web/src/pages/LoopList.tsx`
- Create: `tauri-app/web/src/pages/__tests__/LoopList.test.tsx`
- Modify: `tauri-app/web/src/App.tsx` — replace placeholder with real component

**Interfaces:**
- Consumes: `GET /api/loops` (via fetch), `LoopSummary` type
- Produces: `<LoopList />` page with run/edit/delete actions

- [ ] **Step 1: Write failing test**

Create `tauri-app/web/src/pages/__tests__/LoopList.test.tsx`:
```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LoopList } from "../LoopList";

(window as any).__LC_PORT__ = 5001;

test("shows empty state when no loops", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [],
  } as any);
  render(<MemoryRouter><LoopList /></MemoryRouter>);
  await waitFor(() =>
    expect(screen.getByText(/No loops yet/)).toBeInTheDocument()
  );
});

test("renders loop rows", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [
      { id: "loop1", name: "loop1", loop_type: "coding",
        last_modified: 0, best_score: 0.85, active: false },
    ],
  } as any);
  render(<MemoryRouter><LoopList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText("loop1")).toBeInTheDocument());
  expect(screen.getByText("coding")).toBeInTheDocument();
  expect(screen.getByText("85%")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/LoopList.test.tsx
```
Expected: `Cannot find module '../LoopList'`

- [ ] **Step 3: Implement LoopList page**

Create `tauri-app/web/src/pages/LoopList.tsx`:
```tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LoopSummary, getBaseUrl } from "../types";

export function LoopList() {
  const [loops, setLoops] = useState<LoopSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  async function load() {
    const r = await fetch(`${getBaseUrl()}/api/loops`);
    setLoops(await r.json());
    setLoading(false);
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  async function deleteLoop(id: string) {
    await fetch(`${getBaseUrl()}/api/loops/${id}`, { method: "DELETE" });
    load();
  }

  if (loading) {
    return <div className="p-8 text-muted font-mono text-sm">Loading...</div>;
  }

  if (loops.length === 0) {
    return (
      <div className="p-8 flex flex-col items-center justify-center gap-4 text-center">
        <p className="text-muted font-mono">No loops yet — create one to get started.</p>
        <button
          onClick={() => navigate("/new")}
          className="px-4 py-2 bg-accent-teal text-base rounded font-mono text-sm hover:opacity-90 transition-opacity"
        >
          New Loop
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-primary font-sans font-semibold text-lg">Loops</h1>
        <button
          onClick={() => navigate("/new")}
          className="px-3 py-1.5 bg-accent-teal text-base rounded font-mono text-xs hover:opacity-90"
        >
          + New Loop
        </button>
      </div>
      <div className="space-y-2">
        {loops.map((loop) => (
          <div
            key={loop.id}
            className="bg-surface border border-border-color rounded-lg p-4 flex items-center gap-4"
          >
            {loop.active && (
              <span className="w-2 h-2 rounded-full bg-accent-teal animate-pulse flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-primary font-mono text-sm truncate">{loop.name}</p>
              <span className="text-xs font-mono text-accent-purple">{loop.loop_type}</span>
            </div>
            {loop.best_score !== null && (
              <span className="text-xs font-mono text-accent-teal flex-shrink-0">
                {Math.round(loop.best_score * 100)}%
              </span>
            )}
            <div className="flex gap-2 flex-shrink-0">
              <button
                onClick={() => navigate(`/loops/${loop.id}/run`)}
                className="text-xs font-mono px-2 py-1 border border-accent-teal text-accent-teal rounded hover:bg-accent-teal hover:text-base transition-colors"
              >
                Run
              </button>
              <button
                onClick={() => navigate(`/edit/${loop.id}`)}
                className="text-xs font-mono px-2 py-1 border border-border-color text-muted rounded hover:text-primary transition-colors"
              >
                Edit
              </button>
              <button
                onClick={() => deleteLoop(loop.id)}
                className="text-xs font-mono px-2 py-1 border border-red-800 text-red-400 rounded hover:bg-red-900 transition-colors"
              >
                Del
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Wire into App.tsx**

In `tauri-app/web/src/App.tsx`, add import and replace placeholder:
```tsx
import { LoopList } from "./pages/LoopList";
// ...
<Route path="/loops" element={<LoopList />} />
```

- [ ] **Step 5: Run tests**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/LoopList.test.tsx
```
Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
git add tauri-app/web/src/
git commit -m "feat(sp2): LoopList page with polling and run/edit/delete actions"
```

---

### Task 11: Builder page

**Files:**
- Create: `tauri-app/web/src/pages/Builder.tsx`
- Create: `tauri-app/web/src/pages/__tests__/Builder.test.tsx`
- Modify: `tauri-app/web/src/App.tsx` — replace placeholder

**Interfaces:**
- Consumes: `POST /api/loops`, `GET /api/loops/{id}` (edit mode), `GET /api/context/mcp`
- Produces: `<Builder />` page — 7-section form that saves a `LoopSpec`

- [ ] **Step 1: Write failing tests**

Create `tauri-app/web/src/pages/__tests__/Builder.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Builder } from "../Builder";

(window as any).__LC_PORT__ = 5001;
global.fetch = vi.fn().mockResolvedValue({ json: async () => [] } as any);

test("renders all 7 form sections", () => {
  render(<MemoryRouter><Builder /></MemoryRouter>);
  expect(screen.getByText(/Loop Type/i)).toBeInTheDocument();
  expect(screen.getByText(/Task/i)).toBeInTheDocument();
  expect(screen.getByText(/Goal/i)).toBeInTheDocument();
  expect(screen.getByText(/Context/i)).toBeInTheDocument();
  expect(screen.getByText(/Generator/i)).toBeInTheDocument();
  expect(screen.getByText(/GEPA Params/i)).toBeInTheDocument();
  expect(screen.getByText(/Preview/i)).toBeInTheDocument();
});

test("Save button is present", () => {
  render(<MemoryRouter><Builder /></MemoryRouter>);
  expect(screen.getByText("Save")).toBeInTheDocument();
});
```

- [ ] **Step 2: Implement Builder page**

Create `tauri-app/web/src/pages/Builder.tsx`:
```tsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { LoopSpec, getBaseUrl } from "../types";

const LOOP_TYPES = ["coding", "debugging", "docs", "rfc", "design", "prompt", "custom"] as const;
const CLI_OPTIONS = ["claude", "ollama", "devin"] as const;

function defaultSpec(): LoopSpec {
  return {
    id: `loop-${Date.now()}`,
    type: "coding",
    task: "",
    goal: "",
    generator: { cli: "claude", model: "" },
    judge: { cli: "claude", rubric: "", model: "" },
    context: { project: true, history: true, external: [], mcp_auto_discover: true, project_root: "" },
    gepa: { population_size: 5, top_k: 2, max_generations: 10, fitness_threshold: 0.85, stagnation_limit: 3 },
  };
}

const SECTION_LABEL = "text-xs font-mono text-muted uppercase tracking-widest mb-1";
const INPUT_CLS = "w-full bg-elevated border border-border-color rounded px-3 py-2 text-primary font-mono text-sm focus:outline-none focus:border-accent-teal";

export function Builder() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const [spec, setSpec] = useState<LoopSpec>(defaultSpec());
  const [mcpServers, setMcpServers] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`${getBaseUrl()}/api/context/mcp`)
      .then((r) => r.json())
      .then(setMcpServers)
      .catch(() => {});

    if (id) {
      fetch(`${getBaseUrl()}/api/loops/${id}`)
        .then((r) => r.json())
        .then(setSpec)
        .catch(() => {});
    }
  }, [id]);

  function set<K extends keyof LoopSpec>(key: K, val: LoopSpec[K]) {
    setSpec((s) => ({ ...s, [key]: val }));
  }

  async function save(andRun = false) {
    setSaving(true);
    const r = await fetch(`${getBaseUrl()}/api/loops`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(spec),
    });
    setSaving(false);
    if (r.ok) {
      if (andRun) navigate(`/loops/${spec.id}/run`);
      else navigate("/loops");
    }
  }

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-primary font-sans font-semibold text-lg mb-6">
        {id ? "Edit Loop" : "New Loop"}
      </h1>

      {/* 1. Loop ID */}
      <div className="mb-5">
        <label className={SECTION_LABEL}>Loop ID</label>
        <input className={INPUT_CLS} value={spec.id}
          onChange={(e) => set("id", e.target.value)} />
      </div>

      {/* 2. Loop Type */}
      <div className="mb-5">
        <label className={SECTION_LABEL}>Loop Type</label>
        <div className="grid grid-cols-4 gap-2">
          {LOOP_TYPES.map((t) => (
            <button key={t} onClick={() => set("type", t as LoopSpec["type"])}
              className={`py-2 px-2 rounded border font-mono text-xs transition-colors ${
                spec.type === t
                  ? "border-accent-teal text-accent-teal bg-elevated"
                  : "border-border-color text-muted hover:text-primary"
              }`}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Task */}
      <div className="mb-5">
        <label className={SECTION_LABEL}>Task</label>
        <textarea rows={3} className={INPUT_CLS} value={spec.task}
          placeholder="Describe what you want to accomplish…"
          onChange={(e) => set("task", e.target.value)} />
      </div>

      {/* 4. Goal */}
      <div className="mb-5">
        <label className={SECTION_LABEL}>Goal</label>
        <textarea rows={3} className={INPUT_CLS} value={spec.goal}
          placeholder="What does a perfect output look like?"
          onChange={(e) => set("goal", e.target.value)} />
      </div>

      {/* 5. Context */}
      <div className="mb-5 bg-surface rounded-lg border border-border-color p-4">
        <p className={SECTION_LABEL}>Context</p>
        <label className="flex items-center gap-2 text-sm text-primary font-mono mb-2 cursor-pointer">
          <input type="checkbox" checked={spec.context.project}
            onChange={(e) => set("context", { ...spec.context, project: e.target.checked })} />
          Scrape project context
        </label>
        <label className="flex items-center gap-2 text-sm text-primary font-mono mb-2 cursor-pointer">
          <input type="checkbox" checked={spec.context.history}
            onChange={(e) => set("context", { ...spec.context, history: e.target.checked })} />
          Include iteration history
        </label>
        <label className="block text-xs text-muted font-mono mb-1 mt-2">Project root (leave blank for CWD)</label>
        <input className={INPUT_CLS} value={spec.context.project_root}
          placeholder="/path/to/project"
          onChange={(e) => set("context", { ...spec.context, project_root: e.target.value })} />
        {mcpServers.length > 0 && (
          <div className="mt-3">
            <p className="text-xs text-muted font-mono mb-1">MCP servers (auto-discovered)</p>
            {mcpServers.map((s) => (
              <span key={s} className="inline-block mr-2 mb-1 text-xs font-mono px-2 py-0.5 bg-elevated border border-accent-purple text-accent-purple rounded">
                {s}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 6. Generator / Judge */}
      <div className="mb-5 bg-surface rounded-lg border border-border-color p-4">
        <p className={SECTION_LABEL}>Generator</p>
        <div className="flex gap-2 mb-3">
          {CLI_OPTIONS.map((c) => (
            <button key={c} onClick={() => set("generator", { ...spec.generator, cli: c })}
              className={`flex-1 py-1.5 rounded border font-mono text-xs transition-colors ${
                spec.generator.cli === c
                  ? "border-accent-teal text-accent-teal bg-elevated"
                  : "border-border-color text-muted hover:text-primary"
              }`}>
              {c}
            </button>
          ))}
        </div>
        <input className={INPUT_CLS} value={spec.generator.model}
          placeholder="model name (e.g. sonnet, llama3.2)"
          onChange={(e) => set("generator", { ...spec.generator, model: e.target.value })} />
      </div>

      {/* 7. GEPA Params */}
      <div className="mb-5 bg-surface rounded-lg border border-border-color p-4">
        <p className={SECTION_LABEL}>GEPA Params</p>
        <div className="grid grid-cols-2 gap-3">
          {([
            ["Population size", "population_size"],
            ["Max generations", "max_generations"],
            ["Top-K survivors", "top_k"],
            ["Stagnation limit", "stagnation_limit"],
          ] as const).map(([label, key]) => (
            <div key={key}>
              <label className="text-xs text-muted font-mono">{label}</label>
              <input type="number" className={INPUT_CLS}
                value={spec.gepa[key]}
                onChange={(e) => set("gepa", { ...spec.gepa, [key]: parseInt(e.target.value) || 1 })} />
            </div>
          ))}
          <div className="col-span-2">
            <label className="text-xs text-muted font-mono">Fitness threshold (0–1)</label>
            <input type="number" step="0.05" min="0" max="1" className={INPUT_CLS}
              value={spec.gepa.fitness_threshold}
              onChange={(e) => set("gepa", { ...spec.gepa, fitness_threshold: parseFloat(e.target.value) || 0.85 })} />
          </div>
        </div>
      </div>

      {/* Preview + actions */}
      <div className="mb-5 bg-surface rounded-lg border border-border-color p-4">
        <p className={SECTION_LABEL}>Preview</p>
        <pre className="text-xs font-mono text-muted whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">
          {JSON.stringify(spec, null, 2)}
        </pre>
      </div>

      <div className="flex gap-3">
        <button onClick={() => save(false)} disabled={saving}
          className="px-4 py-2 bg-elevated border border-border-color text-primary font-mono text-sm rounded hover:border-accent-teal transition-colors disabled:opacity-50">
          Save
        </button>
        <button onClick={() => save(true)} disabled={saving}
          className="px-4 py-2 bg-accent-teal text-base font-mono text-sm rounded hover:opacity-90 transition-opacity disabled:opacity-50">
          Save & Run
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire into App.tsx**

```tsx
import { Builder } from "./pages/Builder";
// ...
<Route path="/new" element={<Builder />} />
<Route path="/edit/:id" element={<Builder />} />
```

- [ ] **Step 4: Run tests**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/Builder.test.tsx
```
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tauri-app/web/src/
git commit -m "feat(sp2): Builder page with 7-section form"
```

---

### Task 12: Dashboard page

**Files:**
- Create: `tauri-app/web/src/pages/Dashboard.tsx`
- Create: `tauri-app/web/src/pages/__tests__/Dashboard.test.tsx`
- Modify: `tauri-app/web/src/App.tsx` — replace placeholder

**Interfaces:**
- Consumes: `useLoop()` hook, `EvolutionViewer`, `ResultsPanel`, `GET /api/loops/{id}/best`
- Produces: `<Dashboard />` live run view with stop button

- [ ] **Step 1: Write failing test**

Create `tauri-app/web/src/pages/__tests__/Dashboard.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { Dashboard } from "../Dashboard";

(window as any).__LC_PORT__ = 5001;

test("renders loop id and stop button", () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => ({ content: "" }),
    ok: true,
  } as any);

  render(
    <MemoryRouter initialEntries={["/loops/myloop/run"]}>
      <Routes>
        <Route path="/loops/:id/run" element={<Dashboard />} />
      </Routes>
    </MemoryRouter>
  );
  expect(screen.getByText("myloop")).toBeInTheDocument();
  expect(screen.getByText("Stop")).toBeInTheDocument();
});
```

- [ ] **Step 2: Implement Dashboard page**

Create `tauri-app/web/src/pages/Dashboard.tsx`:
```tsx
import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { EvolutionViewer } from "../components/EvolutionViewer";
import { ResultsPanel } from "../components/ResultsPanel";
import { useLoop } from "../hooks/useLoop";

export function Dashboard() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { events, bestVariant, isRunning, error, run, stop } = useLoop();

  useEffect(() => {
    if (id) run(id);
    return () => stop();
  }, [id]);

  return (
    <div className="p-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-primary font-mono font-semibold">{id}</h1>
          <span className="text-xs text-muted font-mono">
            {isRunning ? "running…" : bestVariant ? "complete" : "idle"}
          </span>
        </div>
        <div className="flex gap-2">
          {isRunning && (
            <button onClick={stop}
              className="px-3 py-1.5 border border-red-700 text-red-400 font-mono text-xs rounded hover:bg-red-900 transition-colors">
              Stop
            </button>
          )}
          <button onClick={() => navigate("/loops")}
            className="px-3 py-1.5 border border-border-color text-muted font-mono text-xs rounded hover:text-primary transition-colors">
            ← Back
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900 border border-red-700 text-red-300 rounded font-mono text-xs">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <EvolutionViewer events={events} isRunning={isRunning} />
        <ResultsPanel bestVariant={bestVariant} />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire into App.tsx**

```tsx
import { Dashboard } from "./pages/Dashboard";
// ...
<Route path="/loops/:id/run" element={<Dashboard />} />
```

- [ ] **Step 4: Run tests**

```bash
cd tauri-app/web && npx vitest run src/pages/__tests__/Dashboard.test.tsx
```
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add tauri-app/web/src/
git commit -m "feat(sp2): Dashboard page with live EvolutionViewer and ResultsPanel"
```

---

### Task 13: FileEditor page + integration wiring + .gitignore + README

**Files:**
- Create: `tauri-app/web/src/pages/FileEditor.tsx`
- Create: `tauri-app/web/src/pages/__tests__/FileEditor.test.tsx`
- Modify: `tauri-app/web/src/App.tsx` — wire FileEditor, remove all Placeholders
- Modify: `.gitignore` — add tauri-app build artifacts
- Modify: `README.md` — add SP2 section

**Interfaces:**
- Consumes: `useFiles()` hook, `@monaco-editor/react`, `GET /api/files`, `GET /api/files/content`, `PUT /api/files/content`

- [ ] **Step 1: Write failing test**

Create `tauri-app/web/src/pages/__tests__/FileEditor.test.tsx`:
```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { FileEditor } from "../FileEditor";

(window as any).__LC_PORT__ = 5001;

// Mock Monaco (heavy, not needed for unit test)
vi.mock("@monaco-editor/react", () => ({
  default: ({ value }: { value: string }) => (
    <textarea data-testid="monaco" defaultValue={value} />
  ),
}));

test("renders path input and file tree heading", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [{ name: "app.py", path: "/p/app.py", is_dir: false }],
  } as any);

  render(<MemoryRouter><FileEditor /></MemoryRouter>);
  expect(screen.getByPlaceholderText(/path/i)).toBeInTheDocument();
  await waitFor(() =>
    expect(screen.getByText("app.py")).toBeInTheDocument()
  );
});
```

- [ ] **Step 2: Implement FileEditor page**

Create `tauri-app/web/src/pages/FileEditor.tsx`:
```tsx
import { useState } from "react";
import MonacoEditor from "@monaco-editor/react";
import { useFiles } from "../hooks/useFiles";
import { FileNode } from "../types";

function getLanguage(path: string): string {
  const ext = path.split(".").pop() ?? "";
  const map: Record<string, string> = {
    py: "python", ts: "typescript", tsx: "typescript",
    js: "javascript", jsx: "javascript", md: "markdown",
    json: "json", yaml: "yaml", yml: "yaml", sh: "shell",
    rs: "rust", toml: "toml",
  };
  return map[ext] ?? "plaintext";
}

function FileTree({ nodes, onSelect }: { nodes: FileNode[]; onSelect: (n: FileNode) => void }) {
  return (
    <ul className="space-y-0.5">
      {nodes.map((n) => (
        <li key={n.path}>
          <button
            onClick={() => !n.is_dir && onSelect(n)}
            className={`w-full text-left px-3 py-1 text-xs font-mono rounded transition-colors ${
              n.is_dir
                ? "text-accent-purple hover:bg-elevated cursor-default"
                : "text-muted hover:text-primary hover:bg-elevated"
            }`}
          >
            {n.is_dir ? "▸ " : "  "}{n.name}
          </button>
        </li>
      ))}
    </ul>
  );
}

export function FileEditor() {
  const { files, content, error, listFiles, readFile, writeFile, setContent } = useFiles();
  const [dirPath, setDirPath] = useState("");
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  async function openDir() {
    if (dirPath) await listFiles(dirPath);
  }

  async function openFile(node: FileNode) {
    setSelectedPath(node.path);
    await readFile(node.path);
    setDirty(false);
  }

  async function save() {
    if (!selectedPath) return;
    setSaving(true);
    await writeFile(selectedPath, content);
    setSaving(false);
    setDirty(false);
  }

  return (
    <div className="flex h-full">
      {/* Left: file tree */}
      <div className="w-56 bg-surface border-r border-border-color flex flex-col flex-shrink-0">
        <div className="p-3 border-b border-border-color">
          <input
            className="w-full bg-elevated border border-border-color rounded px-2 py-1 text-xs font-mono text-primary focus:outline-none focus:border-accent-teal"
            value={dirPath}
            onChange={(e) => setDirPath(e.target.value)}
            placeholder="Enter path…"
            onKeyDown={(e) => e.key === "Enter" && openDir()}
          />
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          <FileTree nodes={files} onSelect={openFile} />
        </div>
      </div>

      {/* Right: editor */}
      <div className="flex-1 flex flex-col">
        {selectedPath && (
          <div className="flex items-center justify-between px-4 py-2 border-b border-border-color bg-surface">
            <span className="text-xs font-mono text-muted">
              {selectedPath}
              {dirty && <span className="ml-2 text-accent-purple">●</span>}
            </span>
            <button
              onClick={save}
              disabled={saving || !dirty}
              className="text-xs font-mono px-3 py-1 bg-accent-teal text-base rounded disabled:opacity-40 hover:opacity-90 transition-opacity"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        )}
        {error && (
          <div className="px-4 py-2 text-xs text-red-400 font-mono bg-red-950">{error}</div>
        )}
        <div className="flex-1">
          <MonacoEditor
            height="100%"
            language={getLanguage(selectedPath ?? "")}
            value={content}
            onChange={(val) => { setContent(val ?? ""); setDirty(true); }}
            theme="vs-dark"
            options={{
              fontFamily: "JetBrains Mono",
              fontSize: 13,
              minimap: { enabled: false },
              padding: { top: 12 },
              scrollBeyondLastLine: false,
            }}
          />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire FileEditor into App.tsx and remove all Placeholders**

Replace `App.tsx` imports and routes (remove the `Placeholder` component entirely):
```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { LoopList } from "./pages/LoopList";
import { Builder } from "./pages/Builder";
import { Dashboard } from "./pages/Dashboard";
import { FileEditor } from "./pages/FileEditor";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-base overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/loops" replace />} />
            <Route path="/loops" element={<LoopList />} />
            <Route path="/loops/:id/run" element={<Dashboard />} />
            <Route path="/new" element={<Builder />} />
            <Route path="/edit/:id" element={<Builder />} />
            <Route path="/files" element={<FileEditor />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
```

- [ ] **Step 4: Run all React tests**

```bash
cd tauri-app/web && npm test
```
Expected: all tests pass (ScoreBar: 2, Sidebar: 1, LoopList: 2, Builder: 2, Dashboard: 1, FileEditor: 1 = **9 passed**)

- [ ] **Step 5: Run all Python server tests**

```bash
cd tauri-app && python -m pytest tests/server/ -v
```
Expected: **12 passed**

- [ ] **Step 6: Update .gitignore**

Add to `/Users/avinashvundyala/Documents/github/skills/.gitignore`:
```
# SP2 Tauri build artifacts
tauri-app/src-tauri/binaries/loop_creator_server-*
tauri-app/dist/
tauri-app/build-tmp/
tauri-app/.venv-build/
tauri-app/web/node_modules/
tauri-app/web/dist/
tauri-app/src-tauri/target/
```

- [ ] **Step 7: Add SP2 section to README**

Add to `README.md` after the existing SP1 content:

```markdown
## Sub-project 2 — macOS Tauri App

A native macOS desktop app that provides a Warp-themed GUI for the loop-creator.

### Prerequisites

- Rust (stable) — `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Node.js 20+
- Tauri CLI — `cargo install tauri-cli --version "^2"`
- Python 3.11+

### Build

```bash
cd tauri-app

# 1. Bundle Python server
bash scripts/build.sh

# 2. Build and launch the Tauri app
cargo tauri dev   # dev mode (requires npm run dev running in tauri-app/web/)
# or
cargo tauri build # production .app + .dmg
```

### Development

```bash
# Terminal 1 — Python server (hot reload)
cd tauri-app && pip install -e ../ fastapi uvicorn
python run_server.py --port 5001

# Terminal 2 — React frontend
cd tauri-app/web && npm run dev

# Terminal 3 — Tauri shell (points at Vite dev server)
cd tauri-app/src-tauri && cargo tauri dev
```

### Running tests

```bash
# Python server tests
cd tauri-app && python -m pytest tests/server/ -v

# React component tests
cd tauri-app/web && npm test
```
```

- [ ] **Step 8: Final commit**

```bash
git add tauri-app/ .gitignore README.md
git commit -m "feat(sp2): FileEditor page, integration wiring, .gitignore, README SP2 section"
```
