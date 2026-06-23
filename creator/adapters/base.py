import time
from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    @abstractmethod
    def call(self, system: str, user: str) -> str: ...

    @abstractmethod
    def call_structured(self, system: str, user: str, schema: dict) -> dict: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    def call_structured_with_retry(
        self, system: str, user: str, schema: dict, retries: int = 2
    ) -> dict:
        last_error: Exception = RuntimeError("No attempts made")
        for attempt in range(retries + 1):
            try:
                return self.call_structured(system, user, schema)
            except (ValueError, Exception) as e:
                last_error = e
                if attempt < retries:
                    time.sleep(2**attempt)
        raise last_error
