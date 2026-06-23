from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Generator

from creator.adapters.base import LLMAdapter
from creator.gepa.judge import Judge
from creator.gepa.mutators import mutate
from creator.spec import GEPAParams

SEED_SYSTEM = (
    "You are an expert AI agent. Given a task description and context, produce the best possible "
    "output for that task. Be specific, thorough, and complete."
)


@dataclass
class Variant:
    prompt: str
    output: str
    score: float
    reason: str
    generation: int = 0


@dataclass
class GenerationEvent:
    generation: int
    variants: list[Variant]
    best_score: float
    event_type: str = "generation"


class GEPAEngine:
    def __init__(self, generator: LLMAdapter, judge: Judge | object,
                 params: GEPAParams, scorer=None, low_score_callback=None):
        self.generator = generator
        self.judge = judge
        self.params = params
        self.scorer = scorer
        self._low_score_callback = low_score_callback
        self._all_variants: list[Variant] = []

    def run(self, task: str, goal: str, context: str = "") -> Generator[GenerationEvent, None, None]:
        ctx_block = f"\n\nContext:\n{context}" if context else ""

        # Generation 0: seed population
        seed_variants = []
        for i in range(self.params.population_size):
            prompt = f"Task: {task}{ctx_block}"
            output = self.generator.call(SEED_SYSTEM, prompt)
            score, reason = self.judge.score(output, goal)
            v = Variant(prompt=prompt, output=output, score=score, reason=reason, generation=0)
            seed_variants.append(v)
            self._all_variants.append(v)

        best_score = max(v.score for v in seed_variants)
        yield GenerationEvent(generation=0, variants=seed_variants, best_score=best_score)

        if best_score >= self.params.fitness_threshold:
            yield GenerationEvent(generation=0, variants=seed_variants,
                                  best_score=best_score, event_type="done")
            return

        stagnation = 0
        low_score_streak = 0
        survivors = sorted(seed_variants, key=lambda v: v.score, reverse=True)[:self.params.top_k]
        last_gen = 0

        for gen in range(1, self.params.max_generations + 1):
            last_gen = gen
            new_variants = []
            ops = self.params.mutation_operators
            for i in range(self.params.population_size):
                parent = survivors[i % len(survivors)]
                op = ops[i % len(ops)]
                if op == "crossover" and len(survivors) >= 2:
                    combined = survivors[0].prompt + "\n---\n" + survivors[1].prompt
                    new_prompt = mutate(self.generator, combined, "crossover", context=context)
                else:
                    new_prompt = mutate(self.generator, parent.prompt, op, context=context)
                output = self.generator.call(SEED_SYSTEM, new_prompt)
                score, reason = self.judge.score(output, goal)
                v = Variant(prompt=new_prompt, output=output, score=score,
                            reason=reason, generation=gen)
                new_variants.append(v)
                self._all_variants.append(v)

            gen_best = max(v.score for v in new_variants)
            if gen_best <= best_score:
                stagnation += 1
            else:
                stagnation = 0
                best_score = gen_best

            if gen_best < 0.4:
                low_score_streak += 1
            else:
                low_score_streak = 0

            if low_score_streak >= 2 and self._low_score_callback:
                self._low_score_callback()
                low_score_streak = 0

            yield GenerationEvent(generation=gen, variants=new_variants, best_score=best_score)

            if best_score >= self.params.fitness_threshold:
                break
            if stagnation >= self.params.stagnation_limit:
                break

            all_candidates = survivors + new_variants
            survivors = sorted(all_candidates, key=lambda v: v.score, reverse=True)[:self.params.top_k]

        best = max(self._all_variants, key=lambda v: v.score)
        yield GenerationEvent(generation=last_gen, variants=[best],
                              best_score=best.score, event_type="done")

    def top_candidates(self, n: int = 3) -> list[Variant]:
        return sorted(self._all_variants, key=lambda v: v.score, reverse=True)[:n]
