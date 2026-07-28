import json
from collections.abc import Iterator

import httpx

from src.config import get_settings


class BackendConnector:
    def __init__(self, api_url: str | None = None, timeout: float = 60.0) -> None:
        self.api_url = api_url or get_settings().backend_api_url
        self.timeout = timeout

    def ask_backend(self, message: str, thread_id: str) -> Iterator[dict[str, str]]:
        try:
            with httpx.stream(
                "POST",
                f"{self.api_url}/chat",
                json={"message": message, "thread_id": thread_id},
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    event = json.loads(line.removeprefix("data: "))
                    yield event
        except GeneratorExit:
            return
