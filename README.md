# creator

A macOS desktop app and CLI for evolving LLM prompts using genetic algorithms (GEPA). Create and iterate on loops, skills, and prompt templates with AI-powered evaluation.

---

## Quick start

```bash
# Install Python package
pip install -e .

# Start dev servers (API + web UI)
./dev.sh start
# → API:  http://localhost:5001
# → App:  http://localhost:5173

# Restart after code changes
./dev.sh restart

# Stop everything
./dev.sh stop

# Tail logs
./dev.sh logs          # all
./dev.sh logs server   # API only
./dev.sh logs web      # Vite only
```

For the native macOS app instead of the browser:

```bash
./dev.sh tauri   # starts API + Vite + Tauri shell
```

---

## CLI

```bash
creator --help

# ── Loops ────────────────────────────────────────────
creator loop run  <id>           # run a loop (streams progress)
creator loop ls                  # list all loops
creator loop new <id>            # wizard to create a new loop
creator loop best <id>           # show best result for a loop

# ── Skills ───────────────────────────────────────────
creator skill run  <name>        # evolve a skill (streams progress)
creator skill ls                 # list saved skills
creator skill new <name>         # interactive skill creator
creator skill publish <name>     # copy SKILL.md → ~/.claude/skills/<name>/
creator skill delete <name>      # delete a skill

# ── Prompts ──────────────────────────────────────────
creator prompt run  <name>       # evolve a prompt (streams progress)
creator prompt ls                # list saved prompts
creator prompt new <name>        # interactive prompt creator
creator prompt fill <name> [k=v …]  # fill template variables and print
creator prompt delete <name>     # delete a prompt

# ── Config ───────────────────────────────────────────
creator config                   # show current config
creator config --whisper-backend openai --openai-api-key sk-...
```

`lc` is an alias for `creator`.

---

## Web UI pages

| URL | Description |
|-----|-------------|
| `/` | Loops list |
| `/loops/new` | Loop builder form |
| `/loops/:id/run` | Loop dashboard (live evolution) |
| `/skills` | Skills list |
| `/skills/new` | Skill builder form |
| `/skills/:name/edit` | Edit a skill spec |
| `/skills/:name/run` | Skill dashboard (live evolution + SKILL.md preview) |
| `/prompts` | Prompts list |
| `/prompts/new` | Prompt builder form |
| `/prompts/:name/edit` | Edit a prompt spec |
| `/prompts/:name/run` | Prompt dashboard (live evolution) |
| `/prompts/:name/use` | Fill template variables → resolved prompt |
| `/settings` | Whisper backend + model + OpenAI key |

---

## REST API

Base URL: `http://localhost:5001`

### Loops
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/loops` | List all loops |
| POST | `/api/loops` | Create loop (body: `LoopSpec`) |
| GET | `/api/loops/:id` | Get loop spec |
| DELETE | `/api/loops/:id` | Delete loop |
| POST | `/api/loops/:id/run` | Run loop — SSE stream of `GenerationEvent` |
| GET | `/api/loops/:id/history` | History as JSON array |
| GET | `/api/loops/:id/best` | Best result markdown |

### Skills
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/skills` | List all skills |
| POST | `/api/skills` | Create skill (body: `SkillSpec`) |
| GET | `/api/skills/:name` | Get skill spec |
| PUT | `/api/skills/:name` | Update skill spec |
| DELETE | `/api/skills/:name` | Delete skill |
| POST | `/api/skills/:name/run` | Run skill — SSE stream |
| GET | `/api/skills/:name/output` | Best SKILL.md content |
| POST | `/api/skills/:name/publish` | Publish to `~/.claude/skills/:name/` |

### Prompts
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/prompts` | List all prompts |
| POST | `/api/prompts` | Create prompt (body: `PromptSpec`) |
| GET | `/api/prompts/:name` | Get prompt spec |
| PUT | `/api/prompts/:name` | Update prompt spec |
| DELETE | `/api/prompts/:name` | Delete prompt |
| POST | `/api/prompts/:name/run` | Run prompt — SSE stream |
| GET | `/api/prompts/:name/output` | Best prompt markdown |
| POST | `/api/prompts/:name/use` | Fill variables → `{"resolved": "..."}` |

### Config & transcription
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/config` | Get `AppConfig` |
| PUT | `/api/config` | Update `AppConfig` |
| POST | `/api/transcribe` | Multipart `audio` file → `{"text": "..."}` |

### SSE event shape

`POST /:id/run` streams `text/event-stream` lines. Each event:

```json
data: {"generation": 1, "variants": [...], "best_score": 0.87, "event_type": "generation"}
```

`event_type` is `"generation"` (intermediate) or `"done"` (final).

---

## Storage

All artifacts live under `~/.creator/`:

```
~/.creator/
  config.yaml          # whisper_backend, whisper_model, openai_api_key
  loops/<id>/
    spec.yaml
    history.jsonl
    best.md
  skills/<name>/
    spec.yaml
    SKILL.md           # best output
  prompts/<name>/
    spec.yaml
    <name>.md          # best output (may contain {{variables}})
```

Published skills are copied to `~/.claude/skills/<name>/SKILL.md`.

---

## Prompt templates

Prompt output files use `{{variable_name}}` placeholders. `fill_prompt` strips YAML frontmatter and replaces all placeholders:

```bash
creator prompt fill code-review language=Python file=main.py
```

---

## Audio / Whisper

The `/api/transcribe` endpoint and `useTranscribe` hook support two backends:

| Backend | Config | Notes |
|---------|--------|-------|
| `local` | `whisper_model: base` | Runs `faster-whisper` locally; no API key needed |
| `openai` | `openai_api_key: sk-...` | Uses OpenAI Whisper API |

Install local transcription: `pip install faster-whisper`

---

## Development setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Rust (stable) — only for the native Tauri app

```bash
# Python packages
pip install -e .                              # creator CLI
pip install -e tauri-app/ fastapi uvicorn     # API server

# Node packages
cd tauri-app/web && npm install

# Tauri CLI (native app only)
cargo install tauri-cli --version "^2"
```

### Tests

```bash
# Creator package (unit tests)
python3 -m pytest tests/ -q

# API server tests
python3 -m pytest tauri-app/tests/ -q

# React component tests
cd tauri-app/web && npm test

# All at once
python3 -m pytest tests/ tauri-app/tests/ -q && cd tauri-app/web && npm test
```

### Production build (native .app + .dmg)

```bash
cd tauri-app

# 1. Bundle the Python server binary
bash scripts/build.sh

# 2. Build the macOS app
cargo tauri build
```

---

## Project layout

```
.
├── creator/              # Python package: CLI, GEPA engine, adapters, runners
│   ├── gepa/             # Genetic/evolutionary prompt algorithm
│   ├── skills/           # Skill spec, registry, runner
│   ├── prompts/          # Prompt spec, registry, runner, fill
│   ├── audio/            # Whisper transcription (local + OpenAI)
│   ├── config.py         # App-level config (~/.creator/config.yaml)
│   └── cli.py            # Typer CLI entry point
├── tauri-app/
│   ├── lc_server/        # FastAPI server (routes, main.py)
│   ├── web/              # React + TypeScript + Vite frontend
│   │   ├── src/pages/    # LoopList, SkillBuilder, PromptDashboard, …
│   │   ├── src/hooks/    # useLoop, useSkill, usePrompt, useTranscribe
│   │   └── src/types.ts  # Shared TS interfaces + getBaseUrl()
│   ├── src-tauri/        # Rust Tauri shell
│   └── run_server.py     # Dev server entry point
├── tests/                # Creator package tests
├── dev.sh                # Start / stop / restart dev servers
└── pyproject.toml        # Creator package metadata
```
