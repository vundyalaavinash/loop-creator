def build_bundle(project: str = "", history: str = "", external: str = "",
                 token_budget: int = 8000) -> str:
    sections = []
    if project:
        sections.append(project)
    if history:
        sections.append(history)
    if external:
        sections.append(f"## External Context\n{external}")
    combined = "\n\n".join(sections)
    # Trim to token budget (approx 4 chars/token)
    max_chars = token_budget * 4
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[... context trimmed to token budget ...]"
    return combined
