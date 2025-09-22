"""InfluxDB helper without external dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

try:  # pragma: no cover
    import requests  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    class _Requests:
        def post(self, *args: Any, **kwargs: Any) -> None:
            return None

    requests = _Requests()  # type: ignore[assignment]


@dataclass
class Point:
    measurement: str
    tags: Dict[str, str] = field(default_factory=dict)
    fields: Dict[str, float] = field(default_factory=dict)

    def tag(self, key: str, value: str) -> "Point":
        self.tags[key] = value
        return self

    def field(self, key: str, value: float) -> "Point":
        self.fields[key] = value
        return self

    def to_line(self) -> str:
        tags = "".join([f",{k}={v}" for k, v in self.tags.items()])
        fields = ",".join([f"{k}={v}" for k, v in self.fields.items()])
        return f"{self.measurement}{tags} {fields}"


class InfluxWriter:
    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self.org = org
        self.bucket = bucket

    def write_points(self, points: Iterable[Point]) -> None:
        lines = "\n".join(point.to_line() for point in points if point.fields)
        if not lines:
            return
        headers = {"Content-Type": "text/plain"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        requests.post(
            f"{self.url}/api/v2/write",
            params={"org": self.org, "bucket": self.bucket, "precision": "s"},
            data=lines.encode("utf-8"),
            headers=headers,
            timeout=10,
        )

    def close(self) -> None:  # pragma: no cover
        return
