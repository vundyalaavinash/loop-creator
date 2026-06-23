import os
import subprocess

KEY_FILES = ["README.md", "pyproject.toml", "package.json", "go.mod",
             "Cargo.toml", "CLAUDE.md", ".env.example", "requirements.txt"]


def scrape_project(root: str) -> str:
    lines = ["## Project Context\n"]
    # Directory tree (max depth 3, exclude common noise)
    tree = _tree(root, max_depth=3)
    lines.append(f"### Directory Tree\n```\n{tree}\n```\n")
    # Key files
    for fname in KEY_FILES:
        path = os.path.join(root, fname)
        if os.path.isfile(path):
            try:
                content = open(path).read()[:2000]
                lines.append(f"### {fname}\n```\n{content}\n```\n")
            except Exception:
                pass
    # Git info
    git_info = _git_info(root)
    if git_info:
        lines.append(f"### Git\n{git_info}\n")
    return "\n".join(lines)


def _tree(root: str, max_depth: int) -> str:
    SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".creator"}
    lines = []
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.replace(root, "").count(os.sep)
        if depth >= max_depth:
            dirnames.clear()
            continue
        dirnames[:] = [d for d in sorted(dirnames) if d not in SKIP]
        indent = "  " * depth
        lines.append(f"{indent}{os.path.basename(dirpath)}/")
        for f in sorted(filenames)[:20]:
            lines.append(f"{indent}  {f}")
    return "\n".join(lines[:100])


def _git_info(root: str) -> str:
    try:
        branch = subprocess.check_output(
            ["git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL, text=True).strip()
        log = subprocess.check_output(
            ["git", "-C", root, "log", "--oneline", "-5"],
            stderr=subprocess.DEVNULL, text=True).strip()
        return f"Branch: {branch}\nRecent commits:\n{log}"
    except Exception:
        return ""
