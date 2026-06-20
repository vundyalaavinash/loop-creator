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
        yield Static(
            f"Loop: {self._spec.id} · Gen 0/{self._spec.gepa.max_generations} · Best: 0.00",
            id="status",
        )
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
            label = "★ " if v.score == event.best_score else f"{chr(65 + i)} "
            table.add_row(label + v.prompt[:60], f"{v.score:.2f}", v.reason[:50])
        self.query_one("#progress-bar", ProgressBar).advance(1)

    def action_stop(self):
        self._stopped.set()
        self.exit()

    def action_pause(self):
        self.notify("Pause not yet supported — press q to stop.", title="Pause")

    def action_show_best(self):
        import os

        best_path = os.path.join(self._loop_dir, "best.md")
        if os.path.isfile(best_path):
            self.notify(open(best_path).read()[:300], title="Best so far")
