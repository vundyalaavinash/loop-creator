import json
import re

from loop_creator.adapters.base import LLMAdapter

JUDGE_SYSTEM = (
    "You are an objective evaluator. Given an AI output and a rubric, score how well "
    "the output meets the rubric. Respond ONLY with a JSON object: "
    '{"score": <float 0.0-1.0>, "reason": "<one sentence>"}'
)


class Judge:
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter

    def score(self, output: str, rubric: str) -> tuple[float, str]:
        user = f"Rubric: {rubric}\n\nOutput to evaluate:\n{output}"
        for _ in range(3):
            try:
                raw = self.adapter.call(JUDGE_SYSTEM, user)
                match = re.search(r"\{.*?\}", raw, re.DOTALL)
                if not match:
                    continue
                data = json.loads(match.group())
                score = max(0.0, min(1.0, float(data["score"])))
                return score, str(data.get("reason", ""))
            except Exception:
                continue
        return 0.0, "parse failed"
