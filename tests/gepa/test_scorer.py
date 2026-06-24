from unittest.mock import MagicMock
from creator.gepa.scorer import Scorer
from creator.adapters.base import LLMAdapter


class MockAdapter(LLMAdapter):
    def call(self, s, u): return '{"clarity":70,"specificity":60,"hallucination_resistance":50}'
    def call_structured(self, s, u, schema): return {"clarity": 70, "specificity": 60, "hallucination_resistance": 50}
    def is_available(self): return True


def test_score_returns_all_dimensions():
    result = Scorer(MockAdapter()).score("Summarize this.")
    assert set(result.keys()) >= {"token_efficiency","format_control","clarity","specificity","hallucination_resistance","overall"}


def test_token_efficiency_penalizes_long_prompts():
    s = Scorer(MockAdapter())
    assert s.score("Summarize.")["token_efficiency"] > s.score("Please provide a very comprehensive and detailed summary of the following long document, making sure to include all key points and nuances. Be thorough.")["token_efficiency"]


def test_format_control_detects_json_instruction():
    s = Scorer(MockAdapter())
    assert s.score("Extract names. Return JSON.")["format_control"] > s.score("Extract names.")["format_control"]


def test_overall_is_average_of_five():
    s = Scorer(MockAdapter())
    r = s.score("Tell me about Python.")
    expected = int((r["token_efficiency"]+r["format_control"]+r["clarity"]+r["specificity"]+r["hallucination_resistance"])/5)
    assert r["overall"] == expected


def test_scores_bounded_0_to_100():
    r = Scorer(MockAdapter()).score("A" * 3000)
    for k, v in r.items():
        assert 0 <= v <= 100, f"{k} out of range: {v}"
