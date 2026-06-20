from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
import yaml

LOOP_TYPES = Literal["coding", "debugging", "docs", "rfc", "design", "prompt", "custom"]
MUTATION_OPS = Literal["rephrase", "expand", "constrain", "crossover"]


class GeneratorSpec(BaseModel):
    cli: str
    model: str = ""


class JudgeSpec(BaseModel):
    cli: str
    rubric: str = ""
    model: str = ""


class ContextSpec(BaseModel):
    project: bool = True
    history: bool = True
    external: list[str] = Field(default_factory=list)
    mcp_auto_discover: bool = True


class GEPAParams(BaseModel):
    population_size: int = 5
    top_k: int = 2
    max_generations: int = 10
    fitness_threshold: float = 0.85
    stagnation_limit: int = 3
    mutation_operators: list[MUTATION_OPS] = Field(
        default_factory=lambda: ["rephrase", "expand", "constrain", "crossover"]
    )


class LoopSpec(BaseModel):
    id: str
    type: LOOP_TYPES
    task: str
    goal: str
    generator: GeneratorSpec
    judge: JudgeSpec
    context: ContextSpec = Field(default_factory=ContextSpec)
    gepa: GEPAParams = Field(default_factory=GEPAParams)


def load_spec(path: str) -> LoopSpec:
    with open(path) as f:
        data = yaml.safe_load(f)
    return LoopSpec(**data)


def save_spec(spec: LoopSpec, path: str) -> None:
    with open(path, "w") as f:
        yaml.dump(spec.model_dump(), f, default_flow_style=False, sort_keys=False)
