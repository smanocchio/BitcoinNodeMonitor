import pytest
import requests

from collector.influx import InfluxWriteError, InfluxWriter, Point


class DummyResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError("boom", response=self)


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
