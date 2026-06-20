from unittest.mock import MagicMock
from loop_creator.gepa.judge import Judge
from loop_creator.adapters.base import LLMAdapter


class GoodAdapter(LLMAdapter):
    def call(self, s, u): return '{"score": 0.82, "reason": "Tests pass"}'
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


class BadAdapter(LLMAdapter):
    def call(self, s, u): return "no json here at all"
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


def test_score_returns_float_and_reason():
    score, reason = Judge(GoodAdapter()).score("output text", "Do tests pass?")
    assert score == 0.82
    assert reason == "Tests pass"


def test_score_clamped_to_0_1():
    class HighAdapter(LLMAdapter):
        def call(self, s, u): return '{"score": 1.5, "reason": "great"}'
        def call_structured(self, s, u, schema): return {}
        def is_available(self): return True
    score, _ = Judge(HighAdapter()).score("out", "rubric")
    assert score <= 1.0


def test_score_returns_zero_on_parse_failure():
    score, reason = Judge(BadAdapter()).score("out", "rubric")
    assert score == 0.0
    assert "parse failed" in reason


def test_rubric_injected_into_prompt():
    calls = []
    class RecordAdapter(LLMAdapter):
        def call(self, s, u):
            calls.append(u)
            return '{"score": 0.5, "reason": "ok"}'
        def call_structured(self, s, u, schema): return {}
        def is_available(self): return True
    Judge(RecordAdapter()).score("my output", "my rubric")
    assert "my rubric" in calls[0]
    assert "my output" in calls[0]
