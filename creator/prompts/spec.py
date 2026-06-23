from pydantic import BaseModel, Field
from creator.spec import GeneratorSpec, JudgeSpec

PROMPT_RUBRICS: dict[str, str] = {
    "commit-message": (
        "The prompt produces clear, conventional commit messages. Evaluate: does it follow "
        "Conventional Commits format, is the subject line under 72 chars, does the body explain why?"
    ),
    "pr-description": (
        "The prompt produces complete PR descriptions. Evaluate: does it summarize the change, "
        "list testing steps, note any breaking changes?"
    ),
    "code-explanation": (
        "The prompt explains code clearly to the target audience. Evaluate: correct abstraction level, "
        "no jargon without definition, concrete examples."
    ),
    "custom": "",
}


class PromptGEPAParams(BaseModel):
    population_size: int = 3
    max_generations: int = 5
    fitness_threshold: float = 0.90


class PromptSpec(BaseModel):
    name: str
    description_goal: str
    variables: list[str] = Field(default_factory=list)
    generator: GeneratorSpec = Field(default_factory=GeneratorSpec)
    judge: JudgeSpec = Field(default_factory=JudgeSpec)
    gepa: PromptGEPAParams = Field(default_factory=PromptGEPAParams)
