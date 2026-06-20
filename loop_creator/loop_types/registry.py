from dataclasses import dataclass, field


@dataclass
class LoopTypeConfig:
    name: str
    judge_rubric_template: str
    context_hints: list[str]
    default_population_size: int = 5
    default_max_generations: int = 10
    default_fitness_threshold: float = 0.85
    uses_scorer: bool = False

    def rubric(self, goal: str) -> str:
        return self.judge_rubric_template.replace("{goal}", goal)


_REGISTRY: dict[str, LoopTypeConfig] = {
    "coding": LoopTypeConfig(
        name="coding",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the output achieve the following goal? '{goal}' "
            "Is the code minimal, clean, and correct? 1.0 = fully achieves goal with clean code."
        ),
        context_hints=["*.py", "*.ts", "*.go", "*.rs", "test_*", "*.test.*", "*.spec.*"],
    ),
    "debugging": LoopTypeConfig(
        name="debugging",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the output correctly identify and fix the issue described in '{goal}'? "
            "Is the root cause explained? Is the fix minimal with no regression risk?"
        ),
        context_hints=["*.log", "*.py", "*.ts", "traceback*", "error*"],
    ),
    "docs": LoopTypeConfig(
        name="docs",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the documentation output satisfy '{goal}'? "
            "Is it accurate, complete, and readable by a new contributor?"
        ),
        context_hints=["README*", "*.md", "docs/", "*.py", "*.ts"],
    ),
    "rfc": LoopTypeConfig(
        name="rfc",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the RFC draft satisfy '{goal}'? "
            "Does it cover: motivation, proposed design, alternatives considered, trade-offs, open questions?"
        ),
        context_hints=["docs/", "*.md", "rfcs/"],
        default_max_generations=8,
    ),
    "design": LoopTypeConfig(
        name="design",
        judge_rubric_template=(
            "Score 0.0–1.0: Does the design document satisfy '{goal}'? "
            "Are components clearly bounded with well-defined interfaces and data flows?"
        ),
        context_hints=["docs/", "*.md", "src/", "*.py", "*.ts"],
    ),
    "prompt": LoopTypeConfig(
        name="prompt",
        judge_rubric_template=(
            "Score 0.0–1.0: Is this prompt clear, specific, grounded, token-efficient, and well-formatted? "
            "Goal: '{goal}'"
        ),
        context_hints=[],
        uses_scorer=True,
        default_population_size=3,
        default_max_generations=5,
    ),
    "custom": LoopTypeConfig(
        name="custom",
        judge_rubric_template="{goal}",
        context_hints=[],
    ),
}


def get_loop_type(type_name: str) -> LoopTypeConfig:
    return _REGISTRY[type_name]
