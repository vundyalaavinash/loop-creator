from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding
from creator.spec import GEPAParams
from creator.loop_types.registry import get_loop_type


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
            classes="title",
        )
        yield Static(f"Population size (variants per generation) — default {d.default_population_size}:")
        yield Input(str(d.default_population_size), id="pop-input")
        yield Static(f"Max generations — default {d.default_max_generations}:")
        yield Input(str(d.default_max_generations), id="gen-input")
        yield Static(
            f"Fitness threshold (0.0–1.0, halt when reached) — default {d.default_fitness_threshold}:"
        )
        yield Input(str(d.default_fitness_threshold), id="thresh-input")
        yield Static(f"Top-K survivors per generation — default {d.default_population_size // 2 or 2}:")
        yield Input("2", id="topk-input")
        yield Static("Stagnation limit (halt after N gens with no improvement) — default 3:")
        yield Input("3", id="stag-input")
        yield Static(
            "[dim]Tip: lower threshold = faster but lower quality. Higher = more iterations.[/dim]",
            classes="tip",
        )
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        try:
            pop = int(self.query_one("#pop-input", Input).value)
            gens = int(self.query_one("#gen-input", Input).value)
            thresh = float(self.query_one("#thresh-input", Input).value)
            top_k = int(self.query_one("#topk-input", Input).value)
            stag = int(self.query_one("#stag-input", Input).value)
        except ValueError:
            return
        params = GEPAParams(
            population_size=max(1, pop),
            top_k=max(1, top_k),
            max_generations=max(1, gens),
            fitness_threshold=max(0.0, min(1.0, thresh)),
            stagnation_limit=max(1, stag),
        )
        self.dismiss(params)
