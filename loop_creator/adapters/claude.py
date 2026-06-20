import json
import re
import shutil
import subprocess

from .base import LLMAdapter


class ClaudeAdapter(LLMAdapter):
    def __init__(self, model: str = "sonnet"):
        self.model = model

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    def call(self, system: str, user: str) -> str:
        result = subprocess.run(
            ["claude", "--print", "--system-prompt", system,
             "--model", self.model, "--output-format", "text", user],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")
        return result.stdout.strip()

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        sys_json = system + "\n\nRespond ONLY with valid JSON matching this schema: " + json.dumps(schema)
        response = self.call(sys_json, user)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {response}")
        return json.loads(match.group())
