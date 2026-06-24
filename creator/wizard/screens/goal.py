from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding

GOAL_EXAMPLES = {
    "coding": "e.g. 'All auth integration tests pass, no 401 errors in logs'",
    "debugging": "e.g. 'Root cause identified, fix applied, all tests green'",
    "docs": "e.g. 'README covers installation, usage, and all public API methods'",
    "rfc": "e.g. 'RFC covers motivation, design, alternatives, and trade-offs'",
    "design": "e.g. 'All components have clear boundaries and defined interfaces'",
    "prompt": "e.g. 'Score >=85 on clarity, specificity, and hallucination resistance'",
    "custom": "e.g. 'Output matches the acceptance criteria defined in the ticket'",
}


class GoalScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, loop_type: str, task: str):
        super().__init__()
        self._loop_type = loop_type
        self._task = task

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Step 3/7 · Success Goal\n\nWhat does 'done' look like for this loop?\n"
            f"This becomes the judge's rubric.\n{GOAL_EXAMPLES.get(self._loop_type, '')}",
            classes="title",
        )
        yield Input(placeholder="Enter success criteria...", id="goal-input")
        yield Static("[dim]Tip: Be measurable. 'Tests pass' is better than 'looks good'.[/dim]", classes="tip")
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        val = self.query_one("#goal-input", Input).value.strip()
        if len(val) < 3:
            return
        self.dismiss(val)
