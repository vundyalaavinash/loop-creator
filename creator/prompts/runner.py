from pathlib import Path

from creator.gepa.engine import GEPAEngine, Variant
from creator.gepa.judge import Judge
from creator.prompts.spec import PromptSpec, PROMPT_RUBRICS
from creator.prompts.registry import prompt_dir as _get_prompt_dir
from creator.spec import GEPAParams
from creator.runner import build_adapter

SEED_SYSTEM_PROMPT = (
    "You are an expert prompt engineer. "
    "Output only the prompt body — no preamble. Use {{variable}} syntax for placeholders."
)


def _prompt_output_path(name: str) -> Path:
    return _get_prompt_dir(name) / f"{name}.md"


def run_prompt(spec: PromptSpec, prompt_dir: Path, on_event=None) -> Variant:
    generator = build_adapter(spec.generator.cli, spec.generator.model)
    judge_adapter = build_adapter(spec.judge.cli, spec.judge.model)

    rubric = PROMPT_RUBRICS.get(spec.judge.rubric or "", "") or spec.judge.rubric or spec.description_goal
    judge = Judge(adapter=judge_adapter)

    params = GEPAParams(
        population_size=spec.gepa.population_size,
        top_k=2,
        max_generations=spec.gepa.max_generations,
        fitness_threshold=spec.gepa.fitness_threshold,
        stagnation_limit=3,
        mutation_operators=["rephrase", "expand", "constrain", "crossover"],
    )

    engine = GEPAEngine(
        generator=generator,
        judge=judge,
        params=params,
        system_prompt=SEED_SYSTEM_PROMPT,
    )

    for event in engine.run(task=spec.description_goal, goal=rubric):
        if on_event:
            on_event(event)

    best = engine.top_candidates(1)[0]
    prompt_dir = Path(prompt_dir)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / f"{spec.name}.md").write_text(best.output)
    return best


def fill_prompt(name: str, variables: dict) -> str:
    template = _prompt_output_path(name).read_text()
    if template.startswith("---"):
        end = template.find("---", 3)
        template = template[end + 3:].lstrip("\n")
    for key, val in variables.items():
        template = template.replace(f"{{{{{key}}}}}", val)
    return template
