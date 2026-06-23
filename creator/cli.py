from __future__ import annotations
import os
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from creator.runner import run_loop, detect_available_adapters
from creator.spec import load_spec, save_spec, LoopSpec, GeneratorSpec, JudgeSpec
from creator.context.history import load_history_summary

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
    try:
        from creator.wizard.app import WizardApp
        result = WizardApp().run()
        if result:
            os.makedirs(LOOPS_DIR, exist_ok=True)
            path = _loop_spec_path(result.id)
            save_spec(result, path)
            console.print(f"[green]Loop saved to {path}[/green]")
            if typer.confirm("Run it now?"):
                _do_run(result)
    except (ImportError, AttributeError):
        console.print("[yellow]Wizard not yet implemented, save spec manually[/yellow]")


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
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Task")
    table.add_column("Best Score")
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
def edit(loop_id: str = typer.Argument(..., help="Loop ID to edit")):
    """Re-open wizard pre-filled with an existing loop spec."""
    spec_path = _loop_spec_path(loop_id)
    if not os.path.isfile(spec_path):
        console.print(f"[red]Loop '{loop_id}' not found at {spec_path}[/red]")
        raise typer.Exit(1)
    try:
        from creator.wizard.app import WizardApp
        existing = load_spec(spec_path)
        result = WizardApp(prefill=existing).run()
        if result:
            save_spec(result, spec_path)
            console.print(f"[green]Loop '{loop_id}' updated.[/green]")
    except ImportError:
        console.print("[yellow]Wizard not available. Edit the spec file directly:[/yellow]")
        console.print(f"  {spec_path}")


@app.command()
def context(loop_id: str = typer.Argument(..., help="Loop ID")):
    """Open the context editor for a loop."""
    try:
        from creator.wizard.app import ContextEditorApp
        spec_path = _loop_spec_path(loop_id)
        if not os.path.isfile(spec_path):
            console.print(f"[red]Loop '{loop_id}' not found at {spec_path}[/red]")
            raise typer.Exit(1)
        spec = load_spec(spec_path)
        updated = ContextEditorApp(spec).run()
        if updated:
            save_spec(updated, spec_path)
            console.print(f"[green]Context updated for {loop_id}[/green]")
    except (ImportError, AttributeError):
        console.print("[yellow]Wizard not yet implemented, save spec manually[/yellow]")


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
        try:
            from creator.wizard.dashboard import DashboardApp
            DashboardApp(spec=spec, loop_dir=loop_dir).run()
        except (ImportError, AttributeError):
            console.print("[yellow]Dashboard not yet implemented, running without watch mode[/yellow]")
            _do_run(spec, watch=False)
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
