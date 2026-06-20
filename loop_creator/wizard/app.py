from __future__ import annotations
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from loop_creator.spec import LoopSpec, GeneratorSpec, JudgeSpec, ContextSpec, GEPAParams
from loop_creator.runner import detect_available_adapters
from loop_creator.wizard.screens.loop_type import LoopTypeScreen
from loop_creator.wizard.screens.task import TaskScreen
from loop_creator.wizard.screens.goal import GoalScreen
from loop_creator.wizard.screens.context_screen import ContextScreen
from loop_creator.wizard.screens.cli_select import CLISelectScreen
from loop_creator.wizard.screens.gepa_params import GEPAParamsScreen
from loop_creator.wizard.screens.preview import PreviewScreen


class WizardApp(App):
    CSS = """
    Screen { background: $surface; }
    .title { color: $accent; text-style: bold; margin-bottom: 1; }
    .tip { color: $text-muted; margin-top: 1; }
    .step-bar { dock: top; height: 1; background: $panel; }
    """
    TITLE = "loop-creator wizard"
    BINDINGS = [("escape", "back", "Back"), ("q", "quit", "Quit")]

    def __init__(self, prefill: LoopSpec | None = None):
        super().__init__()
        self._result: LoopSpec | None = None
        self._state: dict = {}
        self._available = detect_available_adapters()
        self._prefill = prefill

    def on_mount(self):
        self.push_screen(LoopTypeScreen(), self._on_loop_type)

    def _on_loop_type(self, loop_type: str):
        self._state["type"] = loop_type
        self.push_screen(TaskScreen(loop_type), self._on_task)

    def _on_task(self, task: str):
        self._state["task"] = task
        self.push_screen(GoalScreen(self._state["type"], task), self._on_goal)

    def _on_goal(self, goal: str):
        self._state["goal"] = goal
        self.push_screen(ContextScreen(self._state["task"]), self._on_context)

    def _on_context(self, context_spec: ContextSpec):
        self._state["context"] = context_spec
        self.push_screen(CLISelectScreen(self._available), self._on_cli)

    def _on_cli(self, cli_pair: tuple[str, str]):
        gen_cli, judge_cli = cli_pair
        self._state["generator"] = GeneratorSpec(cli=gen_cli)
        self._state["judge"] = JudgeSpec(cli=judge_cli)
        self.push_screen(GEPAParamsScreen(self._state["type"]), self._on_gepa)

    def _on_gepa(self, params: GEPAParams):
        self._state["gepa"] = params
        import re
        import time

        loop_id = re.sub(r"[^a-z0-9-]", "-", self._state["task"][:30].lower()).strip("-")
        loop_id = loop_id or f"loop-{int(time.time())}"
        spec = LoopSpec(
            id=loop_id,
            type=self._state["type"],
            task=self._state["task"],
            goal=self._state["goal"],
            generator=self._state["generator"],
            judge=self._state["judge"],
            context=self._state["context"],
            gepa=self._state["gepa"],
        )
        self.push_screen(PreviewScreen(spec), self._on_preview)

    def _on_preview(self, spec: LoopSpec | None):
        self._result = spec
        self.exit(spec)

    def action_back(self):
        if len(self.screen_stack) > 1:
            self.pop_screen()


class ContextEditorApp(App):
    TITLE = "loop-creator context editor"

    def __init__(self, spec: LoopSpec):
        super().__init__()
        self._spec = spec
        self._result: LoopSpec | None = None

    def on_mount(self):
        self.push_screen(
            ContextScreen(self._spec.task, initial=self._spec.context),
            self._on_done,
        )

    def _on_done(self, context_spec: ContextSpec):
        self._result = self._spec.model_copy(update={"context": context_spec})
        self.exit(self._result)
