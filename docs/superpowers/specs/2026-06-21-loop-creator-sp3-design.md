# Loop Creator SP3 — Skill & Prompt Creator Design

**Date:** 2026-06-21
**Status:** Approved
**Builds on:** SP1 (loop-creator CLI+TUI), SP2 (macOS Tauri App)

---

## Goal

Extend the loop-creator into a general artifact creator that can generate three distinct artifact types — Skills, Prompts, and Loops — each with its own registry, spec format, wizard, and GEPA-powered generation pipeline. Add Whisper speech-to-text so users can describe what they want by voice. Rename the package from `loop_creator` to `creator`.

---

## Module Structure

The existing `loop_creator/` package is renamed to `creator/`. Internal structure:

```
creator/
  cli.py              # Typer app — `creator <type> <action> [options]`
  gepa/               # Unchanged shared GEPA engine
  adapters/           # Unchanged CLI adapters (claude, ollama, devin)
  context/            # Unchanged project context scrapers
  audio/
    recorder.py       # Mic capture → raw audio bytes (via sounddevice)
    whisper.py        # WhisperTranscriber(backend, model) → str
  loops/              # Moved from loop_creator/
    spec.py           # LoopSpec (unchanged)
    registry.py       # ~/.creator/loops/ CRUD
    runner.py         # GEPA runner for loops
    wizard/           # Interactive wizard (unchanged)
  skills/
    spec.py           # SkillSpec dataclass + YAML parse/serialize
    registry.py       # ~/.creator/skills/<name>/ CRUD
    runner.py         # GEPA runner → writes SKILL.md
  prompts/
    spec.py           # PromptSpec dataclass + YAML parse/serialize
    registry.py       # ~/.creator/prompts/<name>.md CRUD
    runner.py         # GEPA runner → writes .md output
```

**Storage locations:**

| Artifact | Path |
|---|---|
| Loops | `~/.creator/loops/<id>.yaml` |
| Skills | `~/.creator/skills/<name>/` (folder with `spec.yaml` + `SKILL.md`) |
| Prompts | `~/.creator/prompts/<name>/` (folder with `spec.yaml` + `<name>.md`) |
| Config | `~/.creator/config.yaml` |

**Config schema (`~/.creator/config.yaml`):**

```yaml
whisper:
  backend: local          # local | openai
  model: base             # faster-whisper model size OR openai model name
  openai_api_key: ""      # only used when backend: openai
```

**pyproject.toml entry points:**

```toml
[project.scripts]
creator = "creator.cli:app"
lc = "creator.cli:app"   # backwards-compat alias
```

---

## Whisper Speech-to-Text

`WhisperTranscriber` is a dependency-injected class so it can be mocked in tests.

```python
class WhisperTranscriber:
    def __init__(self, backend: str = "local", model: str = "base"):
        ...

    def transcribe(self, audio_bytes: bytes) -> str:
        # local: uses faster-whisper
        # openai: calls openai.Audio.transcriptions.create
        ...
```

`audio/recorder.py` captures mic input via `sounddevice` and returns raw PCM bytes. The `--voice` flag on any `new` command:

1. Calls `recorder.py` to capture audio (Ctrl-C to stop)
2. Passes bytes to `WhisperTranscriber.transcribe()`
3. Returns transcribed text string
4. Wizard uses the text as pre-filled answers — user can accept or edit each field

---

## Skill Registry

### SkillSpec

Saved as `~/.creator/skills/<name>/spec.yaml`:

```yaml
name: code-review-ts
description_goal: "Review TypeScript pull requests for correctness, types, and test coverage"
category: code-review
target_platforms:
  - claude-code
generator:
  cli: claude
  model: ""
judge:
  cli: claude
  rubric: ""
gepa:
  population_size: 3
  max_generations: 5
  fitness_threshold: 0.90
```

### SkillTypeConfig — 6 categories

| Category | Judge rubric focus |
|---|---|
| `code-review` | Thoroughness, actionability, false-positive rate |
| `testing` | Coverage completeness, test design quality |
| `documentation` | Clarity, completeness, correct examples |
| `devops` | Safety, idempotency, rollback awareness |
| `data-analysis` | Correctness, insight quality, reproducibility |
| `custom` | User-supplied rubric |

### GEPA configuration

- **task** = `"Write a SKILL.md for a skill that: {description_goal}"`
- **goal** = category rubric
- **seed system prompt** = `"You are an expert at writing Claude Code skills. Output only the SKILL.md content — no preamble or explanation."`

### Output format

AgentSkills-compliant `SKILL.md` written to `~/.creator/skills/<name>/SKILL.md`:

```markdown
---
name: code-review-ts
description: Reviews TypeScript PRs for correctness, types, and test coverage
license: MIT
compatibility:
  - claude-code
---

# Code Review — TypeScript

You are an expert TypeScript engineer performing a thorough code review...
```

### `creator skill publish <name>`

Copies `~/.creator/skills/<name>/SKILL.md` to `~/.claude/skills/<name>/SKILL.md` so it is immediately available in Claude Code.

---

## Prompt Registry

### PromptSpec

Saved as `~/.creator/prompts/<name>/spec.yaml`:

```yaml
name: pr-description-writer
description_goal: "Write structured PR descriptions from a branch name and diff summary"
category: task-instruction
variables:
  - branch_name
  - diff_summary
tags:
  - git
  - documentation
generator:
  cli: claude
  model: ""
judge:
  cli: claude
  rubric: ""
gepa:
  population_size: 3
  max_generations: 5
  fitness_threshold: 0.90
```

### PromptTypeConfig — 5 categories

| Category | Judge rubric focus |
|---|---|
| `system-prompt` | Persona clarity, instruction completeness, constraint coverage |
| `task-instruction` | Action clarity, output format specificity, variable coverage |
| `few-shot` | Example quality, pattern consistency, generalisability |
| `chain-of-thought` | Step sequencing, reasoning explicitness, no-skip completeness |
| `custom` | User-supplied rubric |

### GEPA configuration

- **task** = `"Write a reusable prompt template for: {description_goal}"`
- **goal** = category rubric
- **seed system prompt** = `"You are an expert prompt engineer. Output only the prompt body — no preamble. Use {{variable}} syntax for placeholders."`

### Output format

Markdown with YAML frontmatter written to `~/.creator/prompts/<name>/<name>.md`:

```markdown
---
name: pr-description-writer
description: Generates structured PR descriptions from a diff and branch name
variables:
  - branch_name
  - diff_summary
tags: [git, documentation]
---

You are a technical writer helping developers communicate changes clearly.

Given:
- Branch: {{branch_name}}
- Changes: {{diff_summary}}

Write a PR description with:
1. A one-line summary
2. What changed and why
3. How to test
```

Variables use `{{variable_name}}` syntax — compatible with LangChain, Jinja2, and most prompt runners.

### `creator prompt use <name>`

Interactively fills `{{variables}}` and prints the resolved prompt to stdout (pipeable to clipboard or file).

---

## CLI Command Surface

```
creator <type> <action> [options]

Types:   loop | skill | prompt
Actions: new | list | run | edit | delete
```

Full command table:

| Command | Description |
|---|---|
| `creator loop new [--voice]` | Interactive wizard → LoopSpec |
| `creator loop list` | List loops in `~/.creator/loops/` |
| `creator loop run <id>` | Run GEPA on a loop |
| `creator loop edit <id>` | Open loop spec in `$EDITOR` |
| `creator loop delete <id>` | Remove loop |
| `creator skill new [--voice]` | Wizard → SkillSpec → GEPA → `SKILL.md` |
| `creator skill list` | List skills in `~/.creator/skills/` |
| `creator skill publish <name>` | Copy `SKILL.md` to `~/.claude/skills/<name>/` |
| `creator prompt new [--voice]` | Wizard → PromptSpec → GEPA → `.md` |
| `creator prompt list` | List prompts |
| `creator prompt use <name>` | Fill `{{variables}}` interactively, print result |

**Voice wizard flow:**

```
creator skill new --voice
> 🎤 Listening… (Ctrl-C to cancel)
> Transcribed: "code review skill for TypeScript pull requests"
> Name [code-review-ts]: ▌
> Category [code-review]: ▌
> Target platforms [claude-code]: ▌
> Generating…
```

---

## SP2 Tauri Additions

### New FastAPI routes

| Route | Description |
|---|---|
| `POST /api/transcribe` | `multipart/form-data` audio → `{text: string}` |
| `GET /api/skills` | List SkillSummary objects |
| `POST /api/skills` | Create/update SkillSpec |
| `GET /api/skills/{name}` | Get SkillSpec |
| `DELETE /api/skills/{name}` | Delete skill |
| `POST /api/skills/{name}/run` | Run GEPA → SSE stream |
| `GET /api/skills/{name}/output` | Get `SKILL.md` content |
| `POST /api/skills/{name}/publish` | Copy to `~/.claude/skills/<name>/` |
| `GET /api/prompts` | List PromptSummary objects |
| `POST /api/prompts` | Create/update PromptSpec |
| `GET /api/prompts/{name}` | Get PromptSpec |
| `DELETE /api/prompts/{name}` | Delete prompt |
| `POST /api/prompts/{name}/run` | Run GEPA → SSE stream |
| `GET /api/prompts/{name}/output` | Get generated `.md` content |
| `POST /api/prompts/{name}/use` | Fill `{{variables}}` → resolved string |
| `GET /api/config` | Get `~/.creator/config.yaml` |
| `PUT /api/config` | Save config |

### New React pages

| Page | Route | Description |
|---|---|---|
| `SkillList` | `/skills` | Cards with Run / Edit / Publish / Delete |
| `SkillBuilder` | `/skills/new`, `/skills/:name/edit` | Form: name, description_goal, category, target_platforms, GEPA params, JSON preview |
| `SkillDashboard` | `/skills/:name/run` | Live SSE viewer + `SKILL.md` preview pane |
| `PromptList` | `/prompts` | Cards with Run / Edit / Use / Delete |
| `PromptBuilder` | `/prompts/new`, `/prompts/:name/edit` | Form: name, description_goal, category, variables list, tags, GEPA params |
| `PromptDashboard` | `/prompts/:name/run` | Live SSE viewer + rendered Markdown output |
| `PromptUse` | `/prompts/:name/use` | Fill `{{variable}}` fields → copy-to-clipboard resolved prompt |
| `Settings` | `/settings` | Whisper backend selector, model field, API key field |

### Updated Sidebar

```
── Loops       (existing)
── Skills      (new)
── Prompts     (new)
── Files       (existing)
── Settings    (new)
```

### Voice input in Builder pages

A mic button sits next to each text field. Click → records → calls `POST /api/transcribe` → fills the field. Shows a spinner while transcribing.

**New shared hooks:**
- `useSkill()` — mirrors `useLoop()` for SSE + CRUD
- `usePrompt()` — same pattern
- `useTranscribe()` — `startRecording()` / `stopAndTranscribe()` → returns `{text: string}`

---

## Testing Strategy

### Python server tests (pytest)

| Test file | Covers |
|---|---|
| `tests/server/test_skills.py` | CRUD routes, SSE stream, publish endpoint |
| `tests/server/test_prompts.py` | CRUD routes, SSE stream, `/use` variable substitution |
| `tests/server/test_transcribe.py` | `/transcribe` with mocked `WhisperTranscriber` |
| `tests/server/test_config.py` | GET/PUT config round-trip |
| `tests/creator/test_skill_spec.py` | SkillSpec parse/validate/serialize |
| `tests/creator/test_prompt_spec.py` | PromptSpec + variable extraction |
| `tests/creator/test_whisper.py` | `WhisperTranscriber` with mocked `faster-whisper` |
| `tests/creator/test_prompt_runner.py` | Variable substitution engine |

### React component tests (Vitest + Testing Library)

| Test file | Covers |
|---|---|
| `SkillList.test.tsx` | Empty state, card rows, Publish button |
| `SkillBuilder.test.tsx` | All form sections render, Save present |
| `SkillDashboard.test.tsx` | Skill name shown, Stop button, SSE events |
| `PromptList.test.tsx` | Empty state, card rows |
| `PromptBuilder.test.tsx` | Form sections, variable list add/remove |
| `PromptDashboard.test.tsx` | SSE viewer + Markdown preview pane |
| `PromptUse.test.tsx` | Variable fields rendered, resolved output shown |
| `Settings.test.tsx` | Backend radio, key field, Save |
| `useSkill.test.ts` | SSE accumulation, stop, error |
| `useTranscribe.test.ts` | Mock MediaRecorder, transcribe round-trip |

### Integration tests

- `tests/integration/test_skill_e2e.py` — create SkillSpec → run GEPA (mocked generator) → assert `SKILL.md` written
- `tests/integration/test_prompt_e2e.py` — create PromptSpec → run GEPA → assert `.md` output written

`WhisperTranscriber` is always injected as a dependency — tests mock it to return a canned string; no GPU or network access required.

---

## Dependency additions

| Package | Purpose |
|---|---|
| `faster-whisper` | Local Whisper inference (optional, for `backend: local`) |
| `sounddevice` | Mic capture |
| `openai` | Already present; used for `backend: openai` transcription |
