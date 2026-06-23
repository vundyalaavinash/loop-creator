import json
import re
import shutil
import subprocess

import httpx

from .base import LLMAdapter

DEVIN_API_URL = "https://api.cognition.ai/v1"


class DevinAdapter(LLMAdapter):
    def __init__(self, api_key: str = "", model: str = "devin",
                 base_url: str = DEVIN_API_URL, cli_cmd: str = "devin"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.cli_cmd = cli_cmd
        self._cli_available = shutil.which(cli_cmd) is not None

    def is_available(self) -> bool:
        return self._cli_available or bool(self.api_key)

    def call(self, system: str, user: str) -> str:
        if self._cli_available:
            return self._call_cli(system, user)
        if self.api_key:
            return self._call_api(system, user)
        raise RuntimeError(
            "Devin is not available: `devin` CLI not found on PATH and DEVIN_API_KEY is not set."
        )

    def _call_cli(self, system: str, user: str) -> str:
        result = subprocess.run(
            [self.cli_cmd, "run", "--print", f"{system}\n\n{user}"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"devin CLI error: {result.stderr.strip()}")
        return result.stdout.strip()

    def _call_api(self, system: str, user: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        sys_json = system + "\n\nRespond ONLY with valid JSON matching this schema: " + json.dumps(schema)
        response = self.call(sys_json, user)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {response}")
        return json.loads(match.group())
