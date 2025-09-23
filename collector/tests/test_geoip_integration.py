from __future__ import annotations

from typing import List

import pytest

from collector.config import CollectorConfig
from collector.main import CollectorService


class DummyRPC:
    def __init__(self, peers):
        self._peers = peers

    def get_peer_info(self):
        return self._peers


class DummyInflux:
    def __init__(self) -> None:
        self.points: List = []

    def write_points(self, points):
        self.points = list(points)


class DummyFulcrum:
    def __init__(self, _url: str) -> None:
        return

    def fetch(self):
        return {}


def _base_config(enable_asn: bool) -> CollectorConfig:
    return CollectorConfig(
        enable_process_metrics=False,
        enable_disk_io=False,
        enable_asn_stats=enable_asn,
    )


def _setup_service(monkeypatch, config: CollectorConfig, peers, geoip_factory):
    monkeypatch.setattr("collector.main._build_rpc", lambda _config: DummyRPC(peers))
    influx = DummyInflux()
    monkeypatch.setattr("collector.main._build_influx", lambda _config: influx)
    monkeypatch.setattr("collector.main.FulcrumClient", lambda _url: DummyFulcrum(_url))
    monkeypatch.setattr("collector.main.collect_process_metrics", lambda: pytest.fail("process metrics disabled"))
    monkeypatch.setattr(
        "collector.main.collect_disk_usage", lambda _path: pytest.fail("disk metrics disabled")
    )
    if geoip_factory is not None:
        monkeypatch.setattr("collector.main.GeoIPResolver", geoip_factory)
    else:
        monkeypatch.setattr("collector.main.GeoIPResolver", lambda: pytest.fail("GeoIPResolver should not be used"))

    service = CollectorService(config)
    return service, influx


def test_collect_slow_emits_asn_points_when_enabled(monkeypatch):
    peers = [{"addr": "1.2.3.4:8333"}]

    class DummyResolver:
        def __init__(self) -> None:
            self.lookups = []

        def lookup(self, ip: str):
            self.lookups.append(ip)
            return {"country": "US", "asn": "AS123 Example"}

    resolver = DummyResolver()
    config = _base_config(enable_asn=True)
    service, influx = _setup_service(monkeypatch, config, peers, lambda: resolver)

    service.collect_slow()

    measurements = {point.measurement for point in influx.points}
    assert "peers_asn" in measurements
    asn_points = [p for p in influx.points if p.measurement == "peers_asn"]
    assert asn_points and asn_points[0].tags["asn"] == "AS123 Example"
    assert resolver.lookups == ["1.2.3.4"]


def test_collect_slow_skips_asn_points_when_disabled(monkeypatch):
    peers = [{"addr": "1.2.3.4:8333"}]
    config = _base_config(enable_asn=False)

    service, influx = _setup_service(monkeypatch, config, peers, geoip_factory=None)

    service.collect_slow()

    measurements = {point.measurement for point in influx.points}
    assert "peers_asn" not in measurements
    assert "peers_geo" not in measurements
