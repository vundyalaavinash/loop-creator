import json
import re

import httpx

from .base import LLMAdapter


class OllamaAdapter(LLMAdapter):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    def call(self, system: str, user: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                  "stream": False},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        sys_json = system + "\n\nRespond ONLY with valid JSON matching this schema: " + json.dumps(schema)
        response = self.call(sys_json, user)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {response}")
        return json.loads(match.group())
