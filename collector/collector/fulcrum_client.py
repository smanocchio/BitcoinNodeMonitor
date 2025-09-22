"""Client to pull stats from Fulcrum/Electrs."""

from __future__ import annotations

from typing import Any, Dict

import requests


class FulcrumClient:
    def __init__(self, url: str, timeout: int = 5) -> None:
        self.url = url
        self.timeout = timeout

    def fetch(self) -> Dict[str, Any]:
        response = requests.get(self.url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
