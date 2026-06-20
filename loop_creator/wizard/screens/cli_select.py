from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Select, Button
from textual.binding import Binding


class CLISelectScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, available: list[str]):
        super().__init__()
        self._available = available

    def compose(self) -> ComposeResult:
        if not self._available:
            yield Static("[red]No CLI tools detected. Install claude, devin, or ollama first.[/red]")
            return
        yield Header()
        opts = [(cli, cli) for cli in self._available]
        yield Static(
            "Step 5/7 · CLI Selection\n\nChoose which tool generates outputs and which judges them.\n"
            "Tip: use a fast/cheap model to generate, a smart model to judge.",
            classes="title",
        )
        yield Static("Generator (produces loop outputs):")
        yield Select(opts, id="gen-select", value=self._available[0])
        yield Static("Judge (scores outputs against your goal):")
        yield Select(opts, id="judge-select", value=self._available[-1])
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        gen = self.query_one("#gen-select", Select).value
        judge = self.query_one("#judge-select", Select).value
        self.dismiss((str(gen), str(judge)))
