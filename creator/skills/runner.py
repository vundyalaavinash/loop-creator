from pathlib import Path

from creator.gepa.engine import GEPAEngine, Variant
from creator.gepa.judge import Judge
from creator.skills.spec import SkillSpec, get_rubric
from creator.spec import GEPAParams
from creator.runner import build_adapter

SEED_SYSTEM_SKILL = (
    "You are an expert at writing Claude Code skills. "
    "Output only the SKILL.md content — no preamble or explanation."
)


def run_skill(spec: SkillSpec, skill_dir: Path, on_event=None) -> Variant:
    generator = build_adapter(spec.generator.cli, spec.generator.model)
    judge_adapter = build_adapter(spec.judge.cli, spec.judge.model)

    rubric = get_rubric(spec.category) or spec.judge.rubric or ""
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
        system_prompt=SEED_SYSTEM_SKILL,
    )

    for event in engine.run(task=spec.description_goal, goal=rubric or spec.description_goal):
        if on_event:
            on_event(event)

    best = engine.top_candidates(1)[0]
    skill_dir = Path(skill_dir)
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(best.output)
    return best
