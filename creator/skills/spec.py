from typing import Literal
from pydantic import BaseModel, Field
from creator.spec import GeneratorSpec, JudgeSpec

SKILL_CATEGORIES = ["code-review", "testing", "documentation", "devops", "data-analysis", "custom"]

SKILL_RUBRICS: dict[str, str] = {
    "code-review": (
        "The skill teaches Claude to perform thorough, actionable code review with a low "
        "false-positive rate. Evaluate: does it catch real bugs, does it suggest concrete fixes, "
        "does it avoid nitpicking stylistic preferences, is the tone constructive?"
    ),
    "testing": (
        "The skill teaches Claude to write high-quality tests. Evaluate coverage completeness, "
        "test independence, descriptive failure messages, and avoidance of implementation details."
    ),
    "documentation": (
        "The skill teaches Claude to write clear documentation. Evaluate clarity, completeness, "
        "correct examples, appropriate audience level, and scannable structure."
    ),
    "devops": (
        "The skill teaches Claude to write safe infrastructure scripts. Evaluate safety, "
        "idempotency, rollback awareness, and least-privilege principle."
    ),
    "data-analysis": (
        "The skill teaches Claude to perform rigorous data analysis. Evaluate correctness, "
        "insight quality, reproducibility, and appropriate statistical methods."
    ),
    "custom": "",
}


def get_rubric(category: str) -> str:
    return SKILL_RUBRICS.get(category, "")


class SkillGEPAParams(BaseModel):
    population_size: int = 3
    max_generations: int = 5
    fitness_threshold: float = 0.90


class SkillSpec(BaseModel):
    name: str
    description_goal: str
    category: str
    target_platforms: list[str] = Field(default_factory=lambda: ["claude-code"])
    generator: GeneratorSpec = Field(default_factory=GeneratorSpec)
    judge: JudgeSpec = Field(default_factory=JudgeSpec)
    gepa: SkillGEPAParams = Field(default_factory=SkillGEPAParams)
