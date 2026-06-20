from __future__ import annotations
import os

from loop_creator.adapters.base import LLMAdapter
from loop_creator.adapters.claude import ClaudeAdapter
from loop_creator.adapters.ollama import OllamaAdapter
from loop_creator.adapters.devin import DevinAdapter
from loop_creator.context.project import scrape_project
from loop_creator.context.history import load_history_summary, append_history
from loop_creator.context.external import load_external
from loop_creator.context.bundle import build_bundle
from loop_creator.gepa.engine import GEPAEngine, GenerationEvent, Variant
from loop_creator.gepa.judge import Judge
from loop_creator.gepa.scorer import Scorer
from loop_creator.loop_types.registry import get_loop_type
from loop_creator.spec import LoopSpec


def build_adapter(cli: str, model: str = "") -> LLMAdapter:
    if cli == "claude":
        return ClaudeAdapter(model=model or "sonnet")
    if cli == "ollama":
        return OllamaAdapter(model=model or "llama3.2")
    if cli == "devin":
        return DevinAdapter()
    raise ValueError(f"Unknown CLI: {cli!r}. Supported: claude, ollama, devin")


def detect_available_adapters() -> list[str]:
    adapters = [
        ("claude", ClaudeAdapter()),
        ("ollama", OllamaAdapter()),
        ("devin", DevinAdapter()),
    ]
    return [name for name, a in adapters if a.is_available()]


def run_loop(
    spec: LoopSpec,
    loop_dir: str,
    on_event=None,
) -> Variant:
    os.makedirs(loop_dir, exist_ok=True)
    loop_type = get_loop_type(spec.type)

    generator = build_adapter(spec.generator.cli, spec.generator.model)
    judge_adapter = build_adapter(spec.judge.cli)
    judge = Judge(judge_adapter)

    scorer = None
    if loop_type.uses_scorer:
        scorer = Scorer(judge_adapter)

    # Build context bundle
    ctx_parts = {}
    if spec.context.project:
        ctx_parts["project"] = scrape_project(os.getcwd())
    if spec.context.history:
        ctx_parts["history"] = load_history_summary(loop_dir)
    if spec.context.external:
        ctx_parts["external"] = load_external(spec.context.external)
    context = build_bundle(**ctx_parts)

    goal = spec.goal
    if not spec.judge.rubric:
        goal = loop_type.rubric(spec.goal)

    engine = GEPAEngine(generator=generator, judge=judge, params=spec.gepa, scorer=scorer)

    best: Variant | None = None
    for event in engine.run(task=spec.task, goal=goal, context=context):
        if on_event:
            on_event(event)
        if event.event_type == "done":
            best = event.variants[0]
            for v in event.variants:
                append_history(loop_dir, {
                    "generation": v.generation, "score": v.score,
                    "prompt": v.prompt[:200], "reason": v.reason,
                })

    if best is None:
        best = engine.top_candidates(1)[0]

    best_path = os.path.join(loop_dir, "best.md")
    with open(best_path, "w") as f:
        f.write(
            f"# Best Result\n\n"
            f"Score: {best.score:.3f}\n"
            f"Reason: {best.reason}\n\n"
            f"## Output\n\n{best.output}\n\n"
            f"## Prompt\n\n{best.prompt}\n"
        )

    return best
