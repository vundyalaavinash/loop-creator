from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from creator.runner import run_loop, detect_available_adapters
from creator.spec import load_spec, save_spec, LoopSpec, GeneratorSpec, JudgeSpec

app = typer.Typer(help="Creator — evolve loops, skills, and prompts with GEPA")
loop_app = typer.Typer(help="Manage and run loops")
skill_app = typer.Typer(help="Manage and run skills")
prompt_app = typer.Typer(help="Manage and run prompts")

app.add_typer(loop_app, name="loop")
app.add_typer(skill_app, name="skill")
app.add_typer(prompt_app, name="prompt")

console = Console()

CREATOR_DIR = Path.home() / ".creator"
LOOPS_DIR = CREATOR_DIR / "loops"


def _loop_dir(loop_id: str) -> Path:
    return LOOPS_DIR / loop_id


def _loop_spec_path(loop_id: str) -> Path:
    return LOOPS_DIR / f"{loop_id}.yaml"


# ── Loop commands ──────────────────────────────────────────────────────────────

@loop_app.command("new")
def loop_new():
    """Launch the interactive wizard to build a new loop."""
    try:
        from creator.wizard.app import WizardApp
        result = WizardApp().run()
        if result:
            LOOPS_DIR.mkdir(parents=True, exist_ok=True)
            path = _loop_spec_path(result.id)
            save_spec(result, str(path))
            console.print(f"[green]Loop saved to {path}[/green]")
            if typer.confirm("Run it now?"):
                _do_run(result)
    except (ImportError, AttributeError):
        console.print("[yellow]Wizard not yet implemented, save spec manually[/yellow]")


@loop_app.command("run")
def loop_run(
    loop_id: str = typer.Argument(..., help="Loop ID or path to spec YAML"),
    watch: bool = typer.Option(False, "--watch", help="Show live TUI dashboard"),
    voice: bool = typer.Option(False, "--voice", help="Transcribe task from mic"),
):
    """Run a loop by ID or spec YAML path."""
    # Support both loop ID and direct spec path
    p = Path(loop_id)
    if p.suffix in (".yaml", ".yml") and p.exists():
        spec = load_spec(str(p))
        loop_dir_path = _loop_dir(spec.id)
    else:
        loop_dir_path = _loop_dir(loop_id)
        spec_path = _loop_spec_path(loop_id)
        if not spec_path.exists():
            # Fallback: treat argument as a direct spec path
            spec = load_spec(loop_id)
        else:
            spec = load_spec(str(spec_path))
    if voice:
        spec.task = _transcribe_from_mic()
    _do_run(spec, watch=watch, loop_dir_override=loop_dir_path)


@loop_app.command("list")
def loop_list():
    """List all saved loops."""
    if not LOOPS_DIR.exists():
        typer.echo("No loops yet.")
        return
    for d in sorted(LOOPS_DIR.iterdir()):
        if d.is_dir():
            typer.echo(d.name)


@loop_app.command(name="ls")
def loop_ls():
    """List all saved loops (table view)."""
    if not LOOPS_DIR.exists():
        console.print("[yellow]No loops saved yet. Run 'creator loop new' to create one.[/yellow]")
        return
    table = Table(title="Saved Loops")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Task")
    table.add_column("Best Score")
    for f in sorted(LOOPS_DIR.glob("*.yaml")):
        spec = load_spec(str(f))
        best_path = _loop_dir(spec.id) / "best.md"
        score = "—"
        if best_path.is_file():
            for line in open(best_path):
                if line.startswith("Score:"):
                    score = line.split(":", 1)[1].strip()
                    break
        table.add_row(spec.id, spec.type, spec.task[:50], score)
    console.print(table)


@loop_app.command("history")
def loop_history(loop_id: str = typer.Argument(..., help="Loop ID")):
    """Show evolution history for a loop."""
    from creator.context.history import load_history_summary
    summary = load_history_summary(_loop_dir(loop_id))
    if not summary:
        console.print(f"[yellow]No history found for loop '{loop_id}'[/yellow]")
        return
    console.print(Panel(summary, title=f"History: {loop_id}"))


@loop_app.command("best")
def loop_best(loop_id: str = typer.Argument(..., help="Loop ID")):
    """Print the best result for a loop."""
    path = _loop_dir(loop_id) / "best.md"
    if not path.is_file():
        console.print(f"[red]No best result found for '{loop_id}'. Has this loop been run?[/red]")
        raise typer.Exit(1)
    console.print(open(path).read())


@loop_app.command("edit")
def loop_edit(loop_id: str = typer.Argument(..., help="Loop ID to edit")):
    """Re-open wizard pre-filled with an existing loop spec."""
    spec_path = _loop_spec_path(loop_id)
    if not spec_path.is_file():
        console.print(f"[red]Loop '{loop_id}' not found at {spec_path}[/red]")
        raise typer.Exit(1)
    try:
        from creator.wizard.app import WizardApp
        existing = load_spec(str(spec_path))
        result = WizardApp(prefill=existing).run()
        if result:
            save_spec(result, str(spec_path))
            console.print(f"[green]Loop '{loop_id}' updated.[/green]")
    except ImportError:
        console.print("[yellow]Wizard not available. Edit the spec file directly:[/yellow]")
        console.print(f"  {spec_path}")


@loop_app.command("context")
def loop_context(loop_id: str = typer.Argument(..., help="Loop ID")):
    """Open the context editor for a loop."""
    try:
        from creator.wizard.app import ContextEditorApp
        spec_path = _loop_spec_path(loop_id)
        if not spec_path.is_file():
            console.print(f"[red]Loop '{loop_id}' not found at {spec_path}[/red]")
            raise typer.Exit(1)
        spec = load_spec(str(spec_path))
        updated = ContextEditorApp(spec).run()
        if updated:
            save_spec(updated, str(spec_path))
            console.print(f"[green]Context updated for {loop_id}[/green]")
    except (ImportError, AttributeError):
        console.print("[yellow]Wizard not yet implemented, save spec manually[/yellow]")


def _do_run(spec: LoopSpec, watch: bool = False, loop_dir_override: Optional[Path] = None):
    loop_dir = loop_dir_override or _loop_dir(spec.id)
    available = detect_available_adapters()
    if spec.generator.cli not in available:
        console.print(f"[red]Generator CLI '{spec.generator.cli}' not available. Available: {available}[/red]")
        raise typer.Exit(1)
    if spec.judge.cli not in available:
        console.print(f"[red]Judge CLI '{spec.judge.cli}' not available. Available: {available}[/red]")
        raise typer.Exit(1)

    if watch:
        try:
            from creator.wizard.dashboard import DashboardApp
            DashboardApp(spec=spec, loop_dir=str(loop_dir)).run()
        except (ImportError, AttributeError):
            console.print("[yellow]Dashboard not yet implemented, running without watch mode[/yellow]")
            _do_run(spec, watch=False, loop_dir_override=loop_dir)
    else:
        from rich.progress import Progress, SpinnerColumn, TextColumn
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            ptask = progress.add_task(f"Running loop: {spec.id}", total=spec.gepa.max_generations)

            def on_event(event):
                progress.update(
                    ptask,
                    advance=1,
                    description=f"Gen {event.generation}/{spec.gepa.max_generations} · Best: {event.best_score:.2f}",
                )

            best_variant = run_loop(spec, str(loop_dir), on_event=on_event)

        console.print(Panel(
            f"Score: [green]{best_variant.score:.3f}[/green]\nReason: {best_variant.reason}\n\n{best_variant.output[:500]}",
            title=f"[bold]Best Result — {spec.id}[/bold]",
        ))
        console.print(f"Full result saved to [cyan]{str(loop_dir)}/best.md[/cyan]")


# ── Skill commands ─────────────────────────────────────────────────────────────

@skill_app.command("new")
def skill_new(
    name: str,
    description: str = typer.Option(..., "--description", "-d"),
    category: str = typer.Option("custom", "--category", "-c"),
):
    """Create a new skill spec."""
    from creator.skills.spec import SkillSpec
    from creator.skills.registry import save_skill_spec
    spec = SkillSpec(
        name=name,
        description_goal=description,
        category=category,
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )
    save_skill_spec(spec)
    typer.echo(f"Skill '{name}' created.")


@skill_app.command("run")
def skill_run(
    name: str,
    voice: bool = typer.Option(False, "--voice", help="Transcribe goal from mic"),
):
    """Run GEPA evolution for a skill."""
    from creator.skills.registry import load_skill_spec, skill_dir
    from creator.skills.runner import run_skill
    spec = load_skill_spec(name)
    if voice:
        spec.description_goal = _transcribe_from_mic()
    d = skill_dir(name)
    variant = run_skill(spec, d, on_event=lambda e: typer.echo(f"[gen {e.generation}] best={e.best_score:.2f}"))
    typer.echo(f"\nDone. Best score: {variant.score:.2f}")
    skill_md = d / "SKILL.md"
    if skill_md.exists():
        typer.echo(skill_md.read_text())


@skill_app.command("list")
def skill_list():
    """List all saved skills."""
    from creator.skills.registry import list_skills
    skills = list_skills()
    if not skills:
        typer.echo("No skills yet.")
        return
    for s in skills:
        typer.echo(f"{s['name']}  ({s['category']})")


@skill_app.command("delete")
def skill_delete(name: str):
    """Delete a skill."""
    from creator.skills.registry import delete_skill
    delete_skill(name)
    typer.echo(f"Deleted skill '{name}'.")


@skill_app.command("publish")
def skill_publish(name: str):
    """Publish a skill to ~/.claude/skills/."""
    from creator.skills.registry import publish_skill
    dest = publish_skill(name)
    typer.echo(f"Published to {dest}")


# ── Prompt commands ────────────────────────────────────────────────────────────

@prompt_app.command("new")
def prompt_new(
    name: str,
    description: str = typer.Option(..., "--description", "-d"),
    variables: str = typer.Option("", "--variables", "-v", help="Comma-separated variable names"),
):
    """Create a new prompt spec."""
    from creator.prompts.spec import PromptSpec
    from creator.prompts.registry import save_prompt_spec
    var_list = [v.strip() for v in variables.split(",") if v.strip()]
    spec = PromptSpec(
        name=name,
        description_goal=description,
        variables=var_list,
        generator=GeneratorSpec(cli="claude"),
        judge=JudgeSpec(cli="claude"),
    )
    save_prompt_spec(spec)
    typer.echo(f"Prompt '{name}' created.")


@prompt_app.command("run")
def prompt_run(
    name: str,
    voice: bool = typer.Option(False, "--voice", help="Transcribe goal from mic"),
):
    """Run GEPA evolution for a prompt."""
    from creator.prompts.registry import load_prompt_spec, prompt_dir
    from creator.prompts.runner import run_prompt
    spec = load_prompt_spec(name)
    if voice:
        spec.description_goal = _transcribe_from_mic()
    d = prompt_dir(name)
    variant = run_prompt(spec, d, on_event=lambda e: typer.echo(f"[gen {e.generation}] best={e.best_score:.2f}"))
    typer.echo(f"\nDone. Best score: {variant.score:.2f}")


@prompt_app.command("use")
def prompt_use(
    name: str,
    variables: list[str] = typer.Argument(None, help="key=value pairs"),
):
    """Fill a prompt template with variables and print it."""
    from creator.prompts.runner import fill_prompt
    var_dict = {}
    for item in (variables or []):
        k, _, v = item.partition("=")
        var_dict[k] = v
    result = fill_prompt(name, var_dict)
    typer.echo(result)


@prompt_app.command("list")
def prompt_list():
    """List all saved prompts."""
    from creator.prompts.registry import list_prompts
    prompts = list_prompts()
    if not prompts:
        typer.echo("No prompts yet.")
        return
    for p in prompts:
        typer.echo(f"{p['name']}  — {p['description_goal'][:60]}")


@prompt_app.command("delete")
def prompt_delete(name: str):
    """Delete a prompt."""
    from creator.prompts.registry import delete_prompt
    delete_prompt(name)
    typer.echo(f"Deleted prompt '{name}'.")


# ── Config command ─────────────────────────────────────────────────────────────

@app.command("config")
def config_cmd(
    whisper_backend: Optional[str] = typer.Option(None),
    whisper_model: Optional[str] = typer.Option(None),
    openai_api_key: Optional[str] = typer.Option(None),
):
    """View or update Creator configuration."""
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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _transcribe_from_mic() -> str:
    from creator.audio.recorder import record_audio
    from creator.audio.whisper import WhisperTranscriber
    from creator.config import load_config
    cfg = load_config()
    typer.echo("Recording... press Enter to stop.")
    audio = record_audio()
    t = WhisperTranscriber(
        backend=cfg.whisper_backend,
        model=cfg.whisper_model,
        openai_api_key=cfg.openai_api_key,
    )
    text = t.transcribe(audio)
    typer.echo(f"Transcribed: {text}")
    return text


if __name__ == "__main__":
    app()
