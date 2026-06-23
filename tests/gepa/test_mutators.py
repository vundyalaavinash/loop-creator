from unittest.mock import MagicMock
from creator.gepa.mutators import mutate
from creator.adapters.base import LLMAdapter


class EchoAdapter(LLMAdapter):
    def call(self, s, u): return "mutated prompt result"
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


def test_rephrase_returns_string():
    result = mutate(EchoAdapter(), "original prompt", "rephrase")
    assert isinstance(result, str) and len(result) > 0


def test_expand_returns_string():
    result = mutate(EchoAdapter(), "original prompt", "expand")
    assert isinstance(result, str)


def test_constrain_returns_string():
    result = mutate(EchoAdapter(), "original prompt", "constrain")
    assert isinstance(result, str)


def test_crossover_requires_two_prompts_separated_by_delimiter():
    combined = "prompt A\n---\nprompt B"
    result = mutate(EchoAdapter(), combined, "crossover")
    assert isinstance(result, str)


def test_unknown_operator_raises():
    import pytest
    with pytest.raises(ValueError, match="Unknown operator"):
        mutate(EchoAdapter(), "prompt", "unknown_op")


def test_context_injected_when_provided():
    calls = []
    class RecordAdapter(LLMAdapter):
        def call(self, s, u):
            calls.append(u)
            return "result"
        def call_structured(self, s, u, schema): return {}
        def is_available(self): return True
    mutate(RecordAdapter(), "original", "rephrase", context="important context here")
    assert "important context here" in calls[0]
