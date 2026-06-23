from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label
from textual.binding import Binding

LOOP_TYPES = [
    ("coding",    "Fix, implement, or refactor code"),
    ("debugging", "Track down and resolve a bug"),
    ("docs",      "Write or improve documentation"),
    ("rfc",       "Draft a structured RFC or proposal"),
    ("design",    "Architecture and system design docs"),
    ("prompt",    "Iteratively improve a prompt"),
    ("custom",    "Define your own loop from scratch"),
]

TIPS = {
    "coding": "Works well for targeted tasks like 'migrate all fetch calls to axios'",
    "debugging": "Tip: include error logs in your context for best results",
    "docs": "Tip: add the source file to context so the doc matches the code",
    "rfc": "Tip: attach prior RFCs as external context for consistent format",
    "design": "Tip: add existing architecture docs to context",
    "prompt": "Uses multi-dimensional scoring — no judge CLI needed",
    "custom": "You define the goal and rubric entirely",
}


class LoopTypeScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Step 1/7 · Loop Type\n\nWhat kind of loop are you building?\n"
            "This shapes how context is gathered and how the judge evaluates outputs.",
            classes="title",
        )
        yield ListView(
            *[ListItem(Label(f"  {name:<12} {desc}"), id=name) for name, desc in LOOP_TYPES],
            id="type-list",
        )
        yield Static("", id="tip", classes="tip")
        yield Footer()

    def on_list_view_highlighted(self, event: ListView.Highlighted):
        if event.item:
            t = TIPS.get(event.item.id, "")
            self.query_one("#tip", Static).update(f"Tip: {t}")

    def on_list_view_selected(self, event: ListView.Selected):
        self.dismiss(event.item.id)
