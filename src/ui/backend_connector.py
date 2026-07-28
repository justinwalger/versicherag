import json
from collections.abc import Iterator

import httpx

from src.config import get_ui_settings


class BackendConnector:
    def __init__(self, api_url: str | None = None, timeout: float = 60.0) -> None:
        self.api_url = api_url or get_ui_settings().backend_api_url
        self.timeout = timeout

    def check_password(self, password: str) -> bool | None:
        """Returns True/False for a definite answer, or None if the backend
        couldn't be reached at all."""
        try:
            response = httpx.get(
                f"{self.api_url}/auth/check",
                headers={"X-API-Password": password},
                timeout=self.timeout,
            )
        except httpx.HTTPError:
            return None
        return response.status_code == 200

    def ask_backend(self, message: str, thread_id: str, password: str) -> Iterator[dict[str, str]]:
        try:
            with httpx.stream(
                "POST",
                f"{self.api_url}/chat",
                json={"message": message, "thread_id": thread_id},
                headers={"X-API-Password": password},
                timeout=self.timeout,
            ) as response:
                if response.status_code == 401:
                    yield {"type": "auth_error", "content": "Falsches Passwort."}
                    return
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    event = json.loads(line.removeprefix("data: "))
                    yield event
        except httpx.HTTPError:
            yield {"type": "connection_error", "content": "Server nicht erreichbar."}
        except GeneratorExit:
            return
