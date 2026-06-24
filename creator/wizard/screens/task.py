from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding

EXAMPLES = {
    "coding": "e.g. 'Fix the JWT expiry bug causing 401s after token refresh'",
    "debugging": "e.g. 'Find why the payment service returns 500 on checkout'",
    "docs": "e.g. 'Write a README for the auth module'",
    "rfc": "e.g. 'Draft an RFC for migrating from REST to GraphQL'",
    "design": "e.g. 'Design the caching layer for the API gateway'",
    "prompt": "e.g. 'Improve this prompt: Summarize the document'",
    "custom": "e.g. 'Generate 10 unit test cases for the payment module'",
}


class TaskScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, loop_type: str):
        super().__init__()
        self._loop_type = loop_type

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Step 2/7 · Task Description\n\nDescribe what you want the loop to accomplish.\n"
            f"{EXAMPLES.get(self._loop_type, '')}",
            classes="title",
        )
        yield Input(placeholder="Enter task description...", id="task-input")
        yield Static("", id="validation", classes="tip")
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_input_changed(self, event: Input.Changed):
        if len(event.value.strip()) < 10:
            self.query_one("#validation", Static).update(
                "[yellow]Be specific — longer descriptions produce better loops[/yellow]"
            )
        else:
            self.query_one("#validation", Static).update("[green]✓[/green]")

    def on_button_pressed(self, event: Button.Pressed):
        val = self.query_one("#task-input", Input).value.strip()
        if len(val) < 3:
            self.query_one("#validation", Static).update("[red]Task description is required[/red]")
            return
        self.dismiss(val)
