from loop_creator.adapters.base import LLMAdapter

_SYSTEMS = {
    "rephrase": (
        "Rewrite the prompt below using different wording while keeping the exact same intent. "
        "Return ONLY the rewritten prompt."
    ),
    "expand": (
        "Rewrite the prompt below by adding specificity, constraints, and output format instructions. "
        "Do not change the core intent. Return ONLY the rewritten prompt."
    ),
    "constrain": (
        "Rewrite the prompt below by trimming scope, removing ambiguity, and tightening focus. "
        "Return ONLY the rewritten prompt."
    ),
    "crossover": (
        "You are given two prompt variants separated by '---'. "
        "Splice the best elements from both into a single superior prompt. "
        "Return ONLY the combined prompt."
    ),
}


def mutate(adapter: LLMAdapter, prompt: str, operator: str, context: str = "") -> str:
    if operator not in _SYSTEMS:
        raise ValueError(f"Unknown operator: {operator!r}. Valid: {list(_SYSTEMS)}")
    system = _SYSTEMS[operator]
    ctx_block = f"\n\nProject context:\n{context}" if context else ""
    user = f"{prompt}{ctx_block}"
    return adapter.call(system, user).strip()
