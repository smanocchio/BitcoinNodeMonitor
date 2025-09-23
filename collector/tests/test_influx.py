from typing import cast

import pytest
import requests
from requests import Response

from collector.influx import InfluxWriteError, InfluxWriter, Point


class DummyResponse(Response):
    def __init__(self, status_code: int, text: str = "") -> None:
        super().__init__()
        self.status_code = status_code
        self._content = text.encode()

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError("boom", response=cast(Response, self))


def test_write_points_raises_on_http_error(monkeypatch):
    writer = InfluxWriter("http://localhost:8086", "token", "org", "bucket")

    def _fake_post(*args, **kwargs):
        return DummyResponse(401, "unauthorized")

    monkeypatch.setattr("collector.influx.requests.post", _fake_post)

    with pytest.raises(InfluxWriteError):
        writer.write_points([Point("measurement").field("value", 1)])


def test_write_points_raises_on_connection_error(monkeypatch):
    writer = InfluxWriter("http://localhost:8086", "token", "org", "bucket")

    def _fake_post(*args, **kwargs):
        raise requests.ConnectionError("connection failed")

    monkeypatch.setattr("collector.influx.requests.post", _fake_post)

    with pytest.raises(InfluxWriteError):
        writer.write_points([Point("measurement").field("value", 1)])


def test_write_points_noop_without_fields(monkeypatch):
    writer = InfluxWriter("http://localhost:8086", "token", "org", "bucket")

    called = False

    def _fake_post(*args, **kwargs):
        nonlocal called
        called = True
        return DummyResponse(204, "")

    monkeypatch.setattr("collector.influx.requests.post", _fake_post)

    writer.write_points([Point("measurement")])

    assert called is False


def test_point_to_line_escapes_special_characters():
    line = (
        Point("peer stats")
        .tag("asn", "AS64500 Example")
        .tag("path", "/var/lib/bitcoin,mainnet")
        .field("latency ms", 1.23)
        .field("peers", 8)
        .to_line()
    )

    assert (
        line
        == "peer\\ stats,asn=AS64500\\ Example,path=/var/lib/bitcoin\\,mainnet latency\\ ms=1.23,peers=8"
    )
