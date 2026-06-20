from loop_creator.gepa.engine import GEPAEngine, GenerationEvent, Variant
from loop_creator.gepa.judge import Judge
from loop_creator.gepa.scorer import Scorer
from loop_creator.spec import GEPAParams
from loop_creator.adapters.base import LLMAdapter


class FakeAdapter(LLMAdapter):
    def __init__(self, output="result"):
        self._output = output
    def call(self, s, u): return self._output
    def call_structured(self, s, u, schema): return {}
    def is_available(self): return True


class FakeJudge:
    def score(self, output, rubric): return (0.75, "looks good")


class FakeScorer:
    def score(self, prompt):
        return {"token_efficiency":80,"format_control":50,"clarity":70,
                "specificity":60,"hallucination_resistance":50,"overall":62}


def make_engine(pop=2, gens=2, threshold=0.99) -> GEPAEngine:
    params = GEPAParams(population_size=pop, top_k=1, max_generations=gens,
                        fitness_threshold=threshold, stagnation_limit=5)
    return GEPAEngine(
        generator=FakeAdapter("generated output"),
        judge=FakeJudge(),
        params=params,
    )


def test_run_yields_generation_events():
    engine = make_engine()
    events = list(engine.run("fix bug", "tests pass"))
    assert all(isinstance(e, GenerationEvent) for e in events)


def test_first_event_is_generation_0():
    events = list(make_engine().run("task", "goal"))
    assert events[0].generation == 0


def test_last_event_is_done():
    events = list(make_engine().run("task", "goal"))
    assert events[-1].event_type == "done"


def test_population_size_respected():
    engine = make_engine(pop=3, gens=1)
    events = list(engine.run("task", "goal"))
    gen1 = [e for e in events if e.generation == 1][0]
    assert len(gen1.variants) == 3


def test_stagnation_halts_early():
    params = GEPAParams(population_size=2, top_k=1, max_generations=10,
                        fitness_threshold=0.99, stagnation_limit=2)
    engine = GEPAEngine(generator=FakeAdapter(), judge=FakeJudge(), params=params)
    events = list(engine.run("task", "goal"))
    done = events[-1]
    assert done.event_type == "done"
    assert done.generation < 10


def test_top_candidates_returns_sorted():
    engine = make_engine(pop=2, gens=2)
    list(engine.run("task", "goal"))
    candidates = engine.top_candidates(3)
    scores = [c.score for c in candidates]
    assert scores == sorted(scores, reverse=True)
