# Loop Creator — Design Spec
**Date:** 2026-06-20
**Status:** Approved (updated to reflect MVP integration)

---

## Overview

`loop-creator` is a provider-agnostic, CLI-first tool that builds and runs evolutionary AI loops for any dev activity — coding, debugging, documentation, RFC writing, design docs, prompt improvement, and more. It uses GEPA (Generative Evolutionary Prompt Architecture) to automatically optimize prompts across generations, scoring outputs with a judge LLM until a fitness goal is met.

It works entirely through CLI tools (no API keys required): Claude CLI, Devin CLI, and Ollama. Loop definitions are portable YAML specs that any tool or CI system can execute.

**Foundation:** The core GEPA engine, multi-dimensional scorer, and all three CLI adapters already exist in `/Users/avinashvundyala/Documents/github/mvp`. This project migrates, extends, and wraps that foundation — it does not rewrite it. Estimated savings: ~40-50% of Sub-project 1 build effort.

---

## Sub-Project Roadmap

This design covers **Sub-project 1** only. Sub-projects 2 and 3 each get their own spec.

| # | Sub-project | Description | MVP reuse |
|---|-------------|-------------|-----------|
| 1 | **Core + CLI + TUI** | GEPA engine, CLI adapters, context system, Textual wizard ← this spec | High — adapters, engine, scorer migrated |
| 2 | **macOS Tauri App** | Rich native UI with file viewer/editor, visual loop builder, run dashboard | High — React frontend reused as Tauri web view |
| 3 | **Skill creator extension** | Skill creator module built on the core | Medium — GEPA engine reused |

> **Note:** The prompt creator (Sub-project 3 in the original plan) is considered largely complete via the MVP. It ships as a built-in loop type (`type: prompt`) in Sub-project 1, not a separate sub-project.

---

## Migration from MVP

### What gets migrated as-is

| MVP file | Destination | Notes |
|----------|-------------|-------|
| `backend/src/llm_adapter.py` | `loop_creator/adapters/base.py` | Abstract adapter protocol — no changes |
| `backend/src/claude_adapter.py` | `loop_creator/adapters/claude.py` | Already uses CLI, no API key |
| `backend/src/ollama_adapter.py` | `loop_creator/adapters/ollama.py` | HTTP to local Ollama |
| `backend/src/devin_adapter.py` | `loop_creator/adapters/devin.py` | CLI + REST fallback |
| `backend/src/gepa_engine.py` | `loop_creator/gepa/engine.py` | Core evolutionary loop — extend, don't rewrite |
| `backend/src/scorer.py` | `loop_creator/gepa/scorer.py` | Prompt-specific scorer — used for `type: prompt` loops |
| `backend/tests/` | `tests/` | Migrate all existing tests |
| `frontend/src/` | `tauri-app/web/src/` | Reserved for Sub-project 2 |

### What gets extended

| Component | Extension needed |
|-----------|-----------------|
| `gepa_engine.py` | Add context bundle injection, loop-type-aware mutation, streaming to TUI dashboard |
| `llm_adapter.py` | Add `is_available()` method for auto-detection |
| `scorer.py` | Keep as-is for `type: prompt`; new loop types define their own judge rubric |

### What gets built new

- Context system (project scraper, history, external, MCP discovery)
- Loop spec YAML (schema, loader, validator)
- Textual TUI wizard + live dashboard
- Typer CLI entry point
- Loop type registry (`coding`, `debugging`, `docs`, `rfc`, `design`, `prompt`, `custom`)
- README

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              loop-creator CLI / TUI              │
│         (Typer CLI + Textual wizard)             │
└────────────────────┬────────────────────────────┘
                     │ reads/writes
┌────────────────────▼────────────────────────────┐
│              Loop Spec (YAML)                    │
│  task · goal · type · context_sources ·         │
│  generator_cli · judge_cli · gepa_params        │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │      GEPA Engine        │  ← migrated from mvp/gepa_engine.py
        │  population → score →   │    extended with context injection
        │  select → mutate →      │    and loop-type-aware mutation
        │  next generation        │
        └──┬──────────────────┬───┘
           │                  │
    ┌──────▼──────┐    ┌──────▼──────┐
    │  Generator  │    │    Judge    │
    │  CLI Layer  │    │  CLI Layer  │
    └──┬──────────┘    └──┬──────────┘
       │                  │
  ┌────▼────┐        ┌────▼────┐
  │ claude  │        │ claude  │  ← all 3 adapters migrated from mvp
  │ devin   │        │ devin   │
  │ ollama  │        │ ollama  │
  └─────────┘        └─────────┘
           │
    ┌──────▼──────────────────────┐
    │      Context System         │  ← new
    │  project · history ·        │
    │  external · MCP sources     │
    └─────────────────────────────┘
```

---

## Component 1: CLI Adapter Layer

**Source:** Migrated from `mvp/backend/src/`. All three adapters exist and are tested.

All adapters implement the existing protocol (extended with `is_available()`):

```python
class CLIAdapter(Protocol):
    def run(self, prompt: str, context: str) -> str: ...
    def call_structured(self, system: str, user: str, schema: dict) -> dict: ...
    def is_available(self) -> bool: ...  # new — added for auto-detection
```

### Adapters

**Claude CLI** (`claude_adapter.py`) — already implemented. Uses `claude --print` with no API key. Extended to pass context as part of the system prompt.

**Devin CLI** (`devin_adapter.py`) — already implemented. Dual-mode: CLI (`devin run --print`) with REST API fallback. Uses existing auth, no token needed.

**Ollama** (`ollama_adapter.py`) — already implemented. HTTP to local Ollama server. Model configurable per loop spec.

### Extensibility

New CLIs register as plugins: drop a class implementing the adapter protocol into `~/.loop-creator/adapters/`. The wizard auto-discovers it on next launch.

### Auto-detection

On startup, `loop-creator` calls `is_available()` on each adapter. Only available CLIs are shown in the wizard. If a loop spec names an unavailable CLI, the tool fails fast before wasting any generations.

### Generator vs Judge

Configured independently in the loop spec. Example: Ollama generates at high volume cheaply, Claude judges at high quality.

---

## Component 2: Context System

**Source:** New. No equivalent in the MVP.

Context is assembled into a single structured markdown bundle before each generation and injected into both generator and judge prompts.

### Source Types

**Project context (auto-scraped)**
- Directory tree
- Key files: README, CLAUDE.md, package.json, pyproject.toml, go.mod, etc.
- Detected tech stack
- Git branch + recent commits
- Cached at loop start, refreshed between generations when files change

**Iteration history**
- Every generation's prompt variants, raw outputs, and judge scores appended to `.loop-creator/<loop-id>/history.jsonl`
- A summary of top and bottom performers from prior generations is injected so the mutator knows what already failed

**External context (user-attached)**
- Files, URLs, or raw text attached during the wizard
- Stored as markdown in `.loop-creator/<loop-id>/external/`
- Examples: RFC drafts, ticket descriptions, design docs, Slack threads

**MCP sources (auto-discovered, optional)**
- At startup, reads `~/.claude/settings.json` (and project-level `.claude/settings.json`) to discover configured MCP servers
- If found, lists them in the wizard as toggleable sources — no config knowledge required
- If no MCP servers are present, this section doesn't appear in the wizard

### Auto-population

The wizard actively suggests context based on your task description:
- Scans the repo and matches files to keywords in the task (e.g. "auth" → surfaces auth-related files)
- Pre-fills external context fields with likely candidates
- Each suggestion is a toggle — confirm or dismiss with a keypress

### Inline Editor

Before any generation runs, a context review screen lets you:
- Toggle sources on/off
- Edit any context block inline
- Add new files, URLs, or pasted text
- See live token budget usage (e.g. `1,240 / 8,000 tokens`)
- Re-open at any time with `loop-creator context <loop-id>` or `e` mid-run

---

## Component 3: GEPA Engine

**Source:** Migrated and extended from `mvp/backend/src/gepa_engine.py`.

The MVP engine implements: Pareto front tracking, reflection + mutation (two-step LLM), multi-dimensional scoring via `scorer.py`, and SSE streaming. These are preserved. The following are added:

- **Context injection** — context bundle passed into every generator and judge call
- **Loop-type-aware mutation** — mutation operators vary by loop type (e.g. `type: prompt` uses the existing MVP scorer dimensions; `type: coding` uses test-pass rubric)
- **TUI streaming** — yields events to the Textual dashboard instead of SSE
- **Population-based generation** — MVP runs 1 candidate per generation; extended to N parallel variants (configurable `population_size`)

### Generation Cycle

```
1. Seed        — first generation uses the base prompt from the loop spec
2. Generate    — run N variants through the generator CLI (parallel subprocesses)
3. Score       — judge CLI evaluates each output against the goal, returns 0.0–1.0
4. Select      — top-K variants survive (configurable, default top 2 of 5)
5. Mutate      — survivors are rewritten via 4 operators:
                   Rephrase:   same intent, different wording
                   Expand:     add specificity and constraints
                   Constrain:  trim scope, remove ambiguity
                   Crossover:  splice best segments from two survivors
6. Repeat      — until a stop condition is met
```

### Judge Score Parsing

The judge CLI is prompted with a rubric that ends with: `"Respond with only a JSON object: {\"score\": <float 0.0-1.0>, \"reason\": \"<one sentence>\"}"`. The engine extracts the JSON from stdout using a regex fallback if the response includes surrounding text. If parsing fails after 2 retries, the variant is scored 0.0 and flagged in history.

For `type: prompt` loops, the existing `scorer.py` multi-dimensional scoring (clarity, specificity, hallucination resistance, format control, token efficiency) is used instead of the judge CLI rubric.

### Stop Conditions

Any one of these halts the loop:
- Fitness threshold reached (e.g. score ≥ 0.85)
- Max generations exceeded
- N consecutive generations with no score improvement (stagnation)
- User presses `q` in the TUI

### Low-Score Recovery

If the judge scores all variants below 0.4 for two consecutive generations, the engine pauses and prompts: *"Scores are consistently low — your goal may be too vague. Want to refine it now?"* and opens the goal editor inline.

### Output

The best prompt + output from the winning generation is saved to `.loop-creator/<loop-id>/best.md`. The full evolution history is in `history.jsonl`.

### GEPA Params (loop spec)

```yaml
gepa:
  population_size: 5      # variants per generation
  top_k: 2                # survivors that continue to next generation
  max_generations: 10     # hard cap
  fitness_threshold: 0.85 # halt when any variant hits this score
  stagnation_limit: 3     # halt after N generations with no improvement
  mutation_operators: [rephrase, expand, constrain, crossover]
```

---

## Component 4: Loop Type Registry

**Source:** New. Wraps the engine with type-specific defaults and judge rubrics.

Each loop type is a Python dataclass that provides:
- Default GEPA params
- Default judge rubric template
- Context auto-population hints (which file types to prioritize)
- Mutation operator weights (e.g. `coding` loops weight `constrain` higher)

| Type | Judge rubric focus | Context hints | Notes |
|------|--------------------|---------------|-------|
| `coding` | Tests pass, code is minimal and clean | Source files, test files, lint config | — |
| `debugging` | Root cause identified, fix applied, no regression | Error logs, stack traces, related source | — |
| `docs` | Complete, accurate, readable, matches code | Source files, existing docs | — |
| `rfc` | Covers motivation, design, alternatives, trade-offs | Prior RFCs, design docs, tickets | — |
| `design` | Architecture is clear, components well-bounded | Existing architecture, ADRs | — |
| `prompt` | Clarity, specificity, hallucination resistance, format, token efficiency | None (prompt is self-contained) | Uses MVP `scorer.py` directly |
| `custom` | User-defined rubric | User-defined | No defaults |

---

## Component 5: TUI Wizard + CLI

**Source:** New. No equivalent in the MVP (MVP has a React web UI, not a terminal wizard).

### Design Principles

Every screen has:
- **Header** explaining what this step does and why it matters
- **Inline examples** relevant to what the user has typed so far
- **Smart defaults** pre-filled with explanations
- **`?` help overlay** on any field — plain English + concrete example
- **Inline validation** — feedback as you type, not after submission
- **Back navigation** — `Esc` returns to the previous step, nothing is lost
- **Progress bar** — shows current step and what's remaining

### Wizard Steps

```
Step 1: Loop type        → coding / debugging / docs / RFC / design / prompt / custom
Step 2: Task description → freeform text (what the loop should do)
Step 3: Goal definition  → what "success" looks like (used as judge rubric)
Step 4: Context review   → auto-populated suggestions, toggle/edit/add
Step 5: CLI selection    → generator CLI + judge CLI (only available CLIs shown)
Step 6: GEPA params      → population, generations, threshold (sensible defaults)
Step 7: Preview & launch → full YAML spec preview, save and/or run immediately
```

### Example: Step 1 Screen

```
┌─────────────────────────────────────────────────┐
│ Step 1/7 · Loop Type          [?] Help  [Esc] Back│
│                                                   │
│ What kind of loop are you building?               │
│ This shapes how context is gathered and how       │
│ the judge evaluates outputs.                      │
│                                                   │
│  ▶ Coding          Fix, implement, refactor code  │
│    Debugging       Track down and resolve a bug   │
│    Documentation   Write or improve docs/READMEs  │
│    RFC / Proposal  Draft structured proposals     │
│    Design Doc      Architecture and system design │
│    Prompt          Improve a prompt iteratively   │
│    Custom          Define your own from scratch   │
│                                                   │
│ Tip: Coding loops work well for targeted tasks   │
│ like "migrate all fetch calls to axios"          │
└─────────────────────────────────────────────────┘
```

### Example: Step 4 Context Screen

```
┌─────────────────────────────────────────────────┐
│ Step 4/7 · Context            [?] Help  [Esc] Back│
│                                                   │
│ I found these context sources. Toggle with Space, │
│ edit with Enter, add new with [+].                │
│                                                   │
│ PROJECT (auto-detected)                           │
│  ✓ Directory tree (47 files)                      │
│  ✓ pyproject.toml                                 │
│  ✓ README.md                                      │
│  ○ src/auth/middleware.py  ← suggested match      │
│                                                   │
│ EXTERNAL  [+ Add file / URL / paste text]         │
│  (none yet)                                       │
│                                                   │
│ MCP (1 server detected: filesystem)               │
│  ○ filesystem · read_file                         │
│                                                   │
│ Token budget used: 1,240 / 8,000                  │
└─────────────────────────────────────────────────┘
```

### Live Run Dashboard

```
┌─────────────────────────────────────────────────┐
│ Loop: fix-auth-bug · Gen 3/10 · Best: 0.82 ↑    │
│ [q] Stop  [p] Pause  [e] Edit context  [b] Best │
│                                                   │
│ VARIANT A  score: 0.82 ★                         │
│ "Fix the JWT expiry bug in middleware.py by..."  │
│                                                   │
│ VARIANT B  score: 0.71                            │
│ "Locate and patch the token refresh logic..."    │
│                                                   │
│ VARIANT C  score: 0.65                            │
│ "Rewrite the auth middleware to handle..."       │
│                                                   │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░ 30% · ~7 gens left    │
│ Stagnation: 0/3 · Threshold: 0.85                │
└─────────────────────────────────────────────────┘
```

### CLI Commands

```bash
loop-creator new                      # launch wizard to build a new loop
loop-creator run <spec.yaml>          # run a loop from an existing spec
loop-creator run <spec.yaml> --watch  # live TUI dashboard while running
loop-creator ls                       # list all saved loops with last score
loop-creator history <loop-id>        # show generation-by-generation evolution
loop-creator edit <loop-id>           # re-open wizard pre-filled with existing spec
loop-creator best <loop-id>           # print the winning prompt + output
loop-creator context <loop-id>        # open context editor for an existing loop
```

---

## Loop Spec Format (YAML)

```yaml
id: fix-auth-bug
type: coding
task: "Fix the JWT expiry bug causing 401s after token refresh"
goal: "All auth integration tests pass, no 401 errors in logs"

generator:
  cli: ollama
  model: codellama

judge:
  cli: claude
  rubric: "Score 0.0–1.0: do auth tests pass? Is the fix minimal and clean?"

context:
  project: true
  history: true
  external:
    - docs/auth-design.md
  mcp_auto_discover: true

gepa:
  population_size: 5
  top_k: 2
  max_generations: 10
  fitness_threshold: 0.85
  stagnation_limit: 3
  mutation_operators: [rephrase, expand, constrain, crossover]
```

Example `type: prompt` loop (uses MVP scorer, no judge CLI needed):

```yaml
id: improve-summary-prompt
type: prompt
task: "Improve this prompt: 'Summarize the document'"
goal: "Score ≥ 85 across clarity, specificity, and hallucination resistance"

generator:
  cli: claude

context:
  history: true

gepa:
  population_size: 3
  max_generations: 5
  fitness_threshold: 0.85
```

Specs are portable — any tool that can invoke a subprocess can read and execute them.

---

## Project Structure

```
loop-creator/
├── loop_creator/
│   ├── adapters/
│   │   ├── base.py          # migrated: CLIAdapter protocol (+ is_available)
│   │   ├── claude.py        # migrated: Claude CLI adapter
│   │   ├── devin.py         # migrated: Devin CLI/REST adapter
│   │   └── ollama.py        # migrated: Ollama HTTP adapter
│   ├── context/
│   │   ├── project.py       # new: repo scraper, tech stack detection
│   │   ├── history.py       # new: history.jsonl reader/writer
│   │   ├── external.py      # new: file/URL/paste ingestion
│   │   ├── mcp.py           # new: MCP server discovery from settings.json
│   │   └── bundle.py        # new: assembles all sources into one context block
│   ├── gepa/
│   │   ├── engine.py        # migrated+extended: core generation loop
│   │   ├── scorer.py        # migrated: MVP multi-dimensional scorer (prompt loops)
│   │   ├── mutators.py      # extended: rephrase, expand, constrain, crossover
│   │   ├── judge.py         # new: calls judge CLI, parses score JSON
│   │   └── population.py    # new: parallel variant management, selection
│   ├── loop_types/
│   │   ├── registry.py      # new: loop type lookup
│   │   ├── coding.py        # new: defaults + rubric for coding loops
│   │   ├── debugging.py     # new
│   │   ├── docs.py          # new
│   │   ├── rfc.py           # new
│   │   ├── design.py        # new
│   │   ├── prompt.py        # new: wraps scorer.py (MVP logic)
│   │   └── custom.py        # new: passthrough, user defines everything
│   ├── wizard/
│   │   ├── app.py           # new: Textual app entry point
│   │   ├── screens/
│   │   │   ├── loop_type.py
│   │   │   ├── task.py
│   │   │   ├── goal.py
│   │   │   ├── context.py
│   │   │   ├── cli_select.py
│   │   │   ├── gepa_params.py
│   │   │   └── preview.py
│   │   └── dashboard.py     # new: live run dashboard
│   ├── spec.py              # new: YAML spec loader, validator, serializer
│   └── cli.py               # new: Typer entry point
├── loops/                   # user's saved loop specs
├── .loop-creator/           # runtime state (per loop-id subdirs)
│   └── <loop-id>/
│       ├── history.jsonl
│       ├── best.md
│       ├── context_bundle.md
│       └── external/
├── tauri-app/               # reserved for Sub-project 2
│   └── web/                 # migrated from mvp/frontend/
├── docs/
│   └── README.md
├── tests/                   # migrated from mvp/backend/tests/ + new
└── pyproject.toml
```

---

## README Scope

The README covers:
- Installation and setup (Python 3.11+, CLI prerequisites: claude, devin, ollama)
- Quick start: build your first loop in 2 minutes
- All CLI commands with flags and examples
- Full loop spec field reference with all fields documented
- GEPA params explained in plain English with tuning advice
- Loop type examples: coding, debugging, RFC, design doc, documentation, prompt
- Context system: what each source type does and when to use it
- CLI adapter setup: verifying claude / devin / ollama availability
- Adding custom CLI adapters via plugin directory
- Troubleshooting: low scores, stagnation, context budget exceeded, CLI not found

---

## Out of Scope (Sub-project 1)

- macOS Tauri app (Sub-project 2) — React frontend already exists in MVP, reserved in `tauri-app/`
- Skill creator extension (Sub-project 3)
- Cloud execution / remote agents
- Authentication management for CLI tools
- MVP's FastAPI REST server and SSE endpoint (replaced by TUI streaming)
