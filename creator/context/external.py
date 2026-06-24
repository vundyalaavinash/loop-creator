import os


def load_external(paths: list[str]) -> str:
    parts = []
    for path in paths:
        if path.startswith("http://") or path.startswith("https://"):
            try:
                import httpx
                resp = httpx.get(path, timeout=10.0, follow_redirects=True)
                parts.append(f"### {path}\n{resp.text[:3000]}")
            except Exception as e:
                parts.append(f"### {path}\n[fetch failed: {e}]")
        elif os.path.isfile(path):
            try:
                content = open(path).read()[:3000]
                parts.append(f"### {os.path.basename(path)}\n{content}")
            except Exception as e:
                parts.append(f"### {path}\n[read failed: {e}]")
        else:
            parts.append(f"### {path}\n[not found]")
    return "\n\n".join(parts)
