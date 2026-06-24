import re

import tiktoken

from creator.adapters.base import LLMAdapter

FORMAT_PATTERNS = [
    r"\bjson\b", r"\bmarkdown\b", r"\bbullets?\b", r"\bbullet list\b",
    r"\bnumbered list\b", r"\bformat:\b", r"\bstructured as\b",
    r"\bin the format\b", r"\boutput as\b", r"\breturn (?:a |an )?(?:list|json|dict|array)\b",
    r"\bplain text\b", r"\bcsv\b", r"\bxml\b",
]

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "clarity": {"type": "integer", "minimum": 0, "maximum": 100},
        "specificity": {"type": "integer", "minimum": 0, "maximum": 100},
        "hallucination_resistance": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": ["clarity", "specificity", "hallucination_resistance"],
}

SCORE_SYSTEM = (
    "You are an expert prompt evaluator. Score the given prompt on three dimensions from 0-100:\n"
    "- clarity: How unambiguous and clear is the instruction?\n"
    "- specificity: How specific and constrained is the task?\n"
    "- hallucination_resistance: Does the prompt instruct the model to ground its answer?\n"
    "Return ONLY a JSON object with these three integer fields."
)


class Scorer:
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def score(self, prompt: str) -> dict:
        token_efficiency = self._score_token_efficiency(prompt)
        format_control = self._score_format_control(prompt)
        llm_scores = self.adapter.call_structured_with_retry(
            SCORE_SYSTEM, f"Score this prompt:\n\n{prompt}", SCORE_SCHEMA
        )
        clarity = max(0, min(100, llm_scores["clarity"]))
        specificity = max(0, min(100, llm_scores["specificity"]))
        hr = max(0, min(100, llm_scores["hallucination_resistance"]))
        overall = int((token_efficiency + format_control + clarity + specificity + hr) / 5)
        return {
            "token_efficiency": token_efficiency,
            "format_control": format_control,
            "clarity": clarity,
            "specificity": specificity,
            "hallucination_resistance": hr,
            "overall": overall,
        }

    def _score_token_efficiency(self, prompt: str) -> int:
        count = len(self.tokenizer.encode(prompt)) if self.tokenizer else len(prompt) // 4
        return max(0, min(100, int(100 - (count - 1) / 5)))

    def _score_format_control(self, prompt: str) -> int:
        lower = prompt.lower()
        return min(100, sum(1 for p in FORMAT_PATTERNS if re.search(p, lower)) * 25)
