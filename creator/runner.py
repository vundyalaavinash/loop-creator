from __future__ import annotations
import os

from creator.adapters.base import LLMAdapter
from creator.adapters.claude import ClaudeAdapter
from creator.adapters.ollama import OllamaAdapter
from creator.adapters.devin import DevinAdapter
from creator.context.project import scrape_project
from creator.context.history import load_history_summary, append_history
from creator.context.external import load_external
from creator.context.bundle import build_bundle
from creator.gepa.engine import GEPAEngine, GenerationEvent, Variant
from creator.gepa.judge import Judge
from creator.gepa.scorer import Scorer
from creator.loop_types.registry import get_loop_type
from creator.spec import LoopSpec


def build_adapter(cli: str, model: str = "") -> LLMAdapter:
    if cli == "devin":
        return DevinAdapter()
    if cli == "claude":
        return ClaudeAdapter(model=model or "sonnet")
    if cli == "ollama":
        return OllamaAdapter(model=model or "llama3.2")
    raise ValueError(f"Unknown CLI: {cli!r}. Supported: devin, claude, ollama")


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
    judge_adapter = build_adapter(spec.judge.cli, spec.judge.model)
    judge = Judge(judge_adapter)

    scorer = None
    if loop_type.uses_scorer:
        scorer = Scorer(judge_adapter)

    # Build context bundle
    ctx_parts = {}
    if spec.context.project:
        root = spec.context.project_root or os.getcwd()
        ctx_parts["project"] = scrape_project(root)
    if spec.context.history:
        ctx_parts["history"] = load_history_summary(loop_dir)
    if spec.context.external:
        ctx_parts["external"] = load_external(spec.context.external)
    context = build_bundle(**ctx_parts)

    goal = spec.goal
    if not spec.judge.rubric:
        goal = loop_type.rubric(spec.goal)

    def _low_score_warn():
        import sys
        print("\n⚠️  Scores are consistently low — your goal may be too vague. Consider refining it.", file=sys.stderr)

    engine = GEPAEngine(generator=generator, judge=judge, params=spec.gepa, scorer=scorer, low_score_callback=_low_score_warn)

    def on_event_wrapper(event: GenerationEvent):
        if on_event:
            on_event(event)
        if event.event_type == "generation":
            for v in event.variants:
                append_history(loop_dir, {
                    "generation": v.generation,
                    "score": v.score,
                    "prompt": v.prompt[:200],
                    "reason": v.reason,
                })
        elif event.event_type == "done":
            best_v = event.variants[0]
            best_path = os.path.join(loop_dir, "best.md")
            with open(best_path, "w") as f:
                f.write(
                    f"# Best Result\n\nScore: {best_v.score:.3f}\nReason: {best_v.reason}\n\n"
                    f"## Output\n\n{best_v.output}\n\n## Prompt\n\n{best_v.prompt}\n"
                )

    for event in engine.run(task=spec.task, goal=goal, context=context):
        on_event_wrapper(event)

    return engine.top_candidates(1)[0]
