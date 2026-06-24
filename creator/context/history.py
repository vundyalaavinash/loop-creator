import json
import os


def append_history(loop_dir: str, event: dict) -> None:
    os.makedirs(loop_dir, exist_ok=True)
    path = os.path.join(loop_dir, "history.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")


def load_history_summary(loop_dir: str) -> str:
    path = os.path.join(loop_dir, "history.jsonl")
    if not os.path.isfile(path):
        return ""
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    if not entries:
        return ""
    sorted_entries = sorted(entries, key=lambda e: e.get("score", 0), reverse=True)
    top = sorted_entries[:3]
    bottom = sorted_entries[-3:]
    lines = ["## Prior Iteration History\n### Top performers:"]
    for e in top:
        lines.append(f"- Gen {e.get('generation','?')} score={e.get('score','?')}: {str(e.get('prompt',''))[:80]}")
    lines.append("### Lowest performers:")
    for e in bottom:
        lines.append(f"- Gen {e.get('generation','?')} score={e.get('score','?')}: {str(e.get('prompt',''))[:80]}")
    return "\n".join(lines)
