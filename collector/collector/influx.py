"""InfluxDB helper without external dependencies."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable

import requests
from requests import RequestException, Response

LOGGER = logging.getLogger(__name__)


class InfluxWriteError(RuntimeError):
    """Raised when points cannot be written to InfluxDB."""


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
        measurement = _escape_measurement(self.measurement)
        tags = "".join(
            [f",{_escape_tag_key(k)}={_escape_tag_value(v)}" for k, v in self.tags.items()]
        )
        fields = ",".join([f"{_escape_field_key(k)}={v}" for k, v in self.fields.items()])
        return f"{measurement}{tags} {fields}"


def _escape_measurement(value: str) -> str:
    return _escape_component(str(value), characters=(",", " ", "="))


def _escape_tag_key(value: str) -> str:
    return _escape_component(str(value), characters=(",", " ", "="))


def _escape_tag_value(value: str) -> str:
    return _escape_component(str(value), characters=(",", " ", "="))


def _escape_field_key(value: str) -> str:
    return _escape_component(str(value), characters=(",", " ", "="))


def _escape_component(value: str, characters: tuple[str, ...]) -> str:
    escaped = value.replace("\\", "\\\\")
    for char in characters:
        escaped = escaped.replace(char, f"\\{char}")
    return escaped


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
        try:
            response: Response = requests.post(
                f"{self.url}/api/v2/write",
                params={"org": self.org, "bucket": self.bucket, "precision": "s"},
                data=lines.encode("utf-8"),
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.error(
                "Influx write failed",
                extra={
                    "status_code": getattr(getattr(exc, "response", None), "status_code", None),
                    "response_body": getattr(getattr(exc, "response", None), "text", None),
                },
            )
            raise InfluxWriteError("Failed to write points to InfluxDB") from exc

    def close(self) -> None:  # pragma: no cover
        return
