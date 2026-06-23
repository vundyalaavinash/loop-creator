import json
import os


def discover_mcp_servers() -> list[str]:
    candidates = [
        os.path.expanduser("~/.claude/settings.json"),
        os.path.join(os.getcwd(), ".claude", "settings.json"),
    ]
    names = []
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            data = json.load(open(path))
            servers = data.get("mcpServers", {})
            for name in servers:
                if name not in names:
                    names.append(name)
        except Exception:
            pass
    return names
