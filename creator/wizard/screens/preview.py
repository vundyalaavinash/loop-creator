import yaml
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
from creator.spec import LoopSpec


class PreviewScreen(Screen):
    BINDINGS = [Binding("escape", "app.back", "Back")]

    def __init__(self, spec: LoopSpec):
        super().__init__()
        self._spec = spec

    def compose(self) -> ComposeResult:
        yaml_str = yaml.dump(self._spec.model_dump(), default_flow_style=False, sort_keys=False)
        yield Header()
        yield Static("Step 7/7 · Preview & Launch\n\nYour loop spec:", classes="title")
        yield Static(f"```yaml\n{yaml_str}\n```")
        yield Button("Save & Run", id="run", variant="success")
        yield Button("Save only", id="save", variant="primary")
        yield Button("← Back", id="back", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back":
            self.app.pop_screen()
        else:
            self.dismiss(self._spec)
