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
