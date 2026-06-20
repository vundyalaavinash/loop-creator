# Loop Creator — Sub-project 2: macOS Tauri App

**Status:** Approved  
**Date:** 2026-06-20  
**Depends on:** SP1 (loop-creator CLI + TUI, already shipped)  
**Design reference:** Warp Terminal open-source repo — https://github.com/warpdotdev/warp (UI patterns, colour tokens, layout conventions)

---

## Goal

Wrap the SP1 `loop-creator` Python package in a bundled macOS desktop app (Tauri) that provides a rich GUI for creating, editing, and running GEPA-powered dev loops — and doubles as a companion dashboard for loops started from the terminal. No terminal required to use; no Python install required by the end-user.

---

## Architecture

**Pattern:** Tauri sidecar + FastAPI local server

```
┌─────────────────────────────────────────┐
│           macOS .app bundle             │
│                                         │
│  ┌───────────────┐  ┌────────────────┐  │
│  │  Tauri (Rust) │  │ React webview  │  │
│  │               │  │                │  │
│  │  spawns ──────┼──►  fetch/SSE to  │  │
│  │  sidecar      │  │  localhost:    │  │
│  │  on startup   │  │  <port>        │  │
│  └──────┬────────┘  └───────┬────────┘  │
│         │                   │           │
│  ┌──────▼───────────────────▼────────┐  │
│  │  loop_creator_server (PyInstaller)│  │
│  │  FastAPI + uvicorn                │  │
│  │  ├── POST /api/loops/run  (SSE)   │  │
│  │  ├── GET  /api/loops              │  │
│  │  ├── GET  /api/files/content      │  │
│  │  └── PUT  /api/files/content      │  │
│  │                                   │  │
│  │  imports loop_creator (SP1)       │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

On app launch, Tauri's Rust core spawns `loop_creator_server` (PyInstaller binary) on a random open port, injects the port into the webview as `window.__LC_PORT__`, polls `GET /health` for up to 10 seconds, then shows the window. On app close, the sidecar process is killed.

---

## UI Design — Warp Terminal Theme

The entire UI uses a Warp Terminal-inspired dark aesthetic applied via Tailwind CSS custom config:

| Token | Value | Usage |
|-------|-------|-------|
| `bg-base` | `#1C1C1C` | App background |
| `bg-surface` | `#242424` | Panels, cards |
| `bg-elevated` | `#2E2E2E` | Inputs, hover states |
| `accent-teal` | `#01C7B1` | Primary CTA, active states, progress |
| `accent-purple` | `#9B6DFF` | Secondary highlights, badges |
| `text-primary` | `#F0F0F0` | Main text |
| `text-muted` | `#8A8A8A` | Labels, metadata |
| `border` | `#383838` | Dividers, card outlines |

Font: `JetBrains Mono` (loaded via CSS) for all code, prompts, scores, and mono data. `Inter` for UI labels and body text.

Rounded corners: `8px` panels, `4px` inputs. No drop shadows — use border + background contrast instead.

---

## FastAPI Server Layer

**Location:** `tauri-app/loop_creator/server/`

```
server/
  main.py          # FastAPI app, CORS, --port arg, /health
  routes/
    loops.py       # loop CRUD + SSE run stream
    files.py       # file read/write/list
    context.py     # project context + MCP servers
```

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness check (returns `{"ok": true}`) |
| `POST` | `/api/loops` | Save a new loop spec (body: LoopSpec JSON) |
| `GET` | `/api/loops` | List all loops in `~/.loop-creator/` |
| `GET` | `/api/loops/{id}` | Load a loop spec as JSON |
| `DELETE` | `/api/loops/{id}` | Delete a loop and its directory |
| `POST` | `/api/loops/{id}/run` | Run loop — SSE stream of `GenerationEvent` JSON |
| `GET` | `/api/loops/{id}/history` | Load iteration history (JSONL parsed to JSON array) |
| `GET` | `/api/loops/{id}/best` | Return content of `best.md` |
| `GET` | `/api/files` | List files under `?path=<dir>` (depth 2) |
| `GET` | `/api/files/content` | Read file at `?path=<file>` |
| `PUT` | `/api/files/content` | Write file (body: `{"path": str, "content": str}`) |
| `GET` | `/api/context/project` | Return `scrape_project(path)` for `?path=<dir>` |
| `GET` | `/api/context/mcp` | Return `discover_mcp_servers()` |

**SSE format** (`/api/loops/{id}/run`): Each event is `data: <GenerationEvent JSON>\n\n`. Final event has `event_type: "done"`. This is identical to what `useImprove` in the MVP already consumes.

**Companion monitoring:** `GET /api/loops` scans `~/.loop-creator/*/spec.yaml` and includes `last_modified` timestamp of each loop's `history.jsonl`. The React frontend polls this every 5 seconds and flags any loop modified within the last 60 seconds as "active" — surfacing CLI-started loops in the GUI.

**CORS:** `allow_origins=["tauri://localhost", "http://localhost:*"]` so the Tauri webview and dev Vite server both work.

---

## Tauri Sidecar & Bundling

### File layout

```
tauri-app/
  loop_creator_server.spec      # PyInstaller spec
  scripts/
    build.sh                    # venv + PyInstaller + copy binaries
  src-tauri/
    binaries/                   # gitignored — PyInstaller outputs land here
      loop_creator_server-aarch64-apple-darwin
      loop_creator_server-x86_64-apple-darwin
    src/
      main.rs                   # sidecar lifecycle + port injection
    tauri.conf.json
    Cargo.toml
```

### PyInstaller spec (`loop_creator_server.spec`)

Bundles `loop_creator` package + FastAPI server into a single binary. Collects:
- `loop_creator` (all subpackages)
- `fastapi`, `uvicorn`, `pydantic`, `httpx`, `tiktoken`
- Hidden imports: `uvicorn.logging`, `uvicorn.loops`, `uvicorn.protocols`

Output: `dist/loop_creator_server` (one-file mode). Expected size: 80–120 MB.

### Build script (`scripts/build.sh`)

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install -e ../../     # install loop-creator (SP1)
.venv/bin/pip install fastapi uvicorn pyinstaller
.venv/bin/pyinstaller loop_creator_server.spec
# Copy with Tauri's arch-suffixed naming convention
ARCH=$(uname -m)
cp dist/loop_creator_server \
   src-tauri/binaries/loop_creator_server-${ARCH}-apple-darwin
```

### Tauri main.rs sidecar lifecycle

1. Find a free TCP port (bind to port 0, get assigned port, release)
2. Spawn `loop_creator_server --port <port>` via `tauri::api::process::Command`
3. Poll `GET http://localhost:<port>/health` with 500ms interval, max 10s
4. On ready: inject port via Tauri's Rust `window.eval(format!("window.__LC_PORT__ = {port}"))` API
5. On app exit: send SIGTERM to sidecar PID

### `tauri.conf.json` additions

```json
{
  "tauri": {
    "bundle": {
      "externalBin": ["binaries/loop_creator_server"]
    },
    "allowlist": {
      "shell": { "sidecar": true }
    }
  }
}
```

---

## React Frontend

**Location:** `tauri-app/web/`

Bootstrapped with Vite + React 18 + TypeScript. Tailwind configured with the Warp theme tokens above. JetBrains Mono loaded via `@fontsource/jetbrains-mono`.

### Layout

Fixed left sidebar (240px) with nav icons + labels. Right content area fills remaining space. No top nav bar — Warp-style minimal chrome.

Sidebar items:
- Loops (loop list)
- New Loop (builder)
- File Editor
- Settings (CLI selector, default GEPA params)

### Components reused from MVP (unchanged logic, re-themed)

| Component | Reuse notes |
|-----------|-------------|
| `EvolutionViewer.tsx` | Re-themed to Warp palette; logic unchanged |
| `ResultsPanel.tsx` | Re-themed; unchanged |
| `ScoreBar.tsx` | Teal fill colour (`#01C7B1`); otherwise unchanged |

### New pages

**`pages/LoopList.tsx`**  
Table of all loops: name, type badge (colour-coded), last-run time, best score bar, Run / Edit / Delete actions. Loops active in the last 60s show a pulsing teal dot (companion monitoring). Empty state shows "No loops yet — create one."

**`pages/Builder.tsx`**  
Single-page form replacing the TUI 7-step wizard. Sections:
1. Loop type (7 cards with icon + description; teal border on selection)
2. Task (textarea, monospace, placeholder "Describe what you want to accomplish")
3. Goal (textarea, "What does a perfect output look like?")
4. Context (file paths + URL inputs; "Detect project" button calls `/api/context/project`; MCP toggle auto-populated from `/api/context/mcp`)
5. CLI / model (dropdown: claude / ollama / devin; model name input)
6. GEPA params (sliders for population 2–10, generations 1–20, fitness 0.5–1.0; numeric inputs for top-k, stagnation limit)
7. Preview (read-only YAML of the spec; Save, Save & Run buttons)

On Save: `POST /api/loops` → navigate to LoopList.  
On Save & Run: `POST /api/loops` → `POST /api/loops/{id}/run` → navigate to Dashboard.

**`pages/Dashboard.tsx`**  
Live run view. Top bar: loop name, type badge, stop button (aborts SSE), elapsed timer. Main area: `EvolutionViewer` (generation cards stream in). Bottom: `ResultsPanel` (populated on `done` event). If navigated to an already-finished loop, loads history and best result statically.

**`pages/FileEditor.tsx`**  
Left pane: file tree (calls `GET /api/files?path=<dir>`; path input at top; depth-2 tree). Right pane: Monaco editor (`@monaco-editor/react`), language auto-detected from extension. Save button: `PUT /api/files/content`. Unsaved-changes indicator (orange dot on tab).

### New hooks

**`hooks/useLoop.ts`** — adapted from MVP's `useImprove`:
- `run(loopId)` opens SSE to `http://localhost:${window.__LC_PORT__}/api/loops/${loopId}/run`
- Returns `{ events, bestResult, isRunning, error, stop }`
- `stop()` closes the EventSource

**`hooks/useFiles.ts`**:
- `listFiles(path)` → `GET /api/files?path=<path>`
- `readFile(path)` → `GET /api/files/content?path=<path>`
- `writeFile(path, content)` → `PUT /api/files/content`

### `types.ts` additions (on top of MVP types)

```typescript
export interface LoopSummary {
  id: string;
  name: string;
  loop_type: string;
  last_modified: number;   // epoch seconds
  best_score: number | null;
  active: boolean;         // modified within last 60s
}

export interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  children?: FileNode[];
}
```

---

## Project File Structure

```
tauri-app/
  loop_creator/
    server/
      __init__.py
      main.py
      routes/
        __init__.py
        loops.py
        files.py
        context.py
  web/
    src/
      components/
        EvolutionViewer.tsx    # reused
        ResultsPanel.tsx       # reused
        ScoreBar.tsx           # reused
        Sidebar.tsx            # new
      pages/
        LoopList.tsx
        Builder.tsx
        Dashboard.tsx
        FileEditor.tsx
      hooks/
        useLoop.ts
        useFiles.ts
      types.ts
      App.tsx
      main.tsx
    package.json
    tailwind.config.js        # Warp theme tokens
    vite.config.ts
  loop_creator_server.spec
  scripts/
    build.sh
  src-tauri/
    binaries/                 # gitignored
    src/
      main.rs
    tauri.conf.json
    Cargo.toml
```

---

## Testing Strategy

**FastAPI server (pytest):**
- `TestClient` smoke tests for every endpoint
- SSE run endpoint: mock `run_loop` to yield 3 fake events, assert SSE format
- File endpoints: use `tmp_path` fixture

**React (Vitest + React Testing Library):**
- `Builder.tsx`: renders all 7 sections, form fields present
- `LoopList.tsx`: renders empty state; renders loop rows
- `Dashboard.tsx`: mounts with mock SSE events, EvolutionViewer receives them
- `ScoreBar.tsx`, `ResultsPanel.tsx`: snapshot tests

**Manual integration (macOS):**
- Build app, launch, verify sidecar starts (no white screen)
- Create a loop via Builder, run it, see live GEPA events
- Edit a context file in FileEditor, save, verify on disk
- Start a loop from the terminal CLI, verify it appears as "active" in LoopList

---

## Sub-project Roadmap

| SP | Name | Status |
|----|------|--------|
| 1 | Core CLI + TUI | ✅ Shipped |
| **2** | **macOS Tauri App** | **This spec** |
| 3 | Skill creator extension | Future |

---

## Out of Scope (SP2)

- Windows / Linux builds
- Auto-update (Tauri updater)
- Loop sharing / export
- Multi-user or cloud sync
- SP3 skill creator
