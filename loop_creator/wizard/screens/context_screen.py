from __future__ import annotations
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Checkbox, Input, Button
from textual.binding import Binding
from loop_creator.spec import ContextSpec
from loop_creator.context.mcp import discover_mcp_servers


class ContextScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, task: str, initial: ContextSpec | None = None):
        super().__init__()
        self._task = task
        self._initial = initial or ContextSpec()
        self._mcp_servers = discover_mcp_servers()
        self._external_paths: list[str] = list(self._initial.external)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Step 4/7 · Context\n\nToggle sources with Space, add new with the input below.\n"
            "The more relevant context, the better the loop performs.",
            classes="title",
        )
        yield Checkbox("Project files (auto-detected)", value=self._initial.project, id="ctx-project")
        yield Checkbox("Iteration history (what worked/failed before)", value=self._initial.history, id="ctx-history")
        yield Static("[dim]── External ──[/dim]")
        for path in self._external_paths:
            yield Static(f"  ✓ {path}")
        yield Input(placeholder="Add file path or URL...", id="external-input")
        if self._mcp_servers:
            yield Static("[dim]── MCP Servers (auto-discovered) ──[/dim]")
            for name in self._mcp_servers:
                yield Checkbox(f"MCP: {name}", value=False, id=f"mcp-{name}")
        yield Static("", id="token-budget", classes="tip")
        yield Button("Next →", id="next", variant="primary")
        yield Footer()

    def on_mount(self):
        self._update_budget()

    def _update_budget(self):
        estimate = 500
        if self.query_one("#ctx-project", Checkbox).value:
            estimate += 2000
        estimate += len(self._external_paths) * 500
        self.query_one("#token-budget", Static).update(
            f"[dim]Estimated context: ~{estimate:,} / 8,000 tokens[/dim]"
        )

    def on_checkbox_changed(self, event: Checkbox.Changed):
        self._update_budget()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "next":
            ext_input = self.query_one("#external-input", Input).value.strip()
            if ext_input:
                self._external_paths.append(ext_input)
            spec = ContextSpec(
                project=self.query_one("#ctx-project", Checkbox).value,
                history=self.query_one("#ctx-history", Checkbox).value,
                external=self._external_paths,
                mcp_auto_discover=True,
            )
            self.dismiss(spec)
