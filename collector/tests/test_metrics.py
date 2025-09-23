from collector.config import CollectorConfig
from collector.metrics import (
    ReorgTracker,
    bucket_mempool_histogram,
    create_peer_geo_points,
    peers_metrics,
    percentile,
)
from collector.metrics import _extract_ip


def test_reorg_tracker():
    tracker = ReorgTracker(max_depth=5)
    for height in [100, 101, 102, 99, 100]:
        tracker.update(height)
    assert tracker.max_reorg_depth() == 3


def test_percentile():
    values = [10, 20, 30, 40, 50]
    assert percentile(values, 0.95) >= 40


def test_bucket_histogram():
    raw = {"0-5": 10, "5-10": 2}
    buckets = bucket_mempool_histogram(raw)
    assert any(bucket["bucket"] == "0-5" for bucket in buckets)


def test_peer_metrics():
    peers = [
        {"inbound": True, "pingtime": 0.1},
        {"inbound": False, "pingtime": 0.2},
        {"inbound": False, "pingtime": 0.3},
    ]
    summary = peers_metrics(peers)
    assert summary["total"] == 3
    assert summary["inbound"] == 1
    assert summary["outbound"] == 2
    assert summary["ping_p95_ms"] >= summary["ping_avg_ms"]


def test_extract_ip_handles_ipv4_and_ipv6():
    assert _extract_ip("203.0.113.1:8333") == "203.0.113.1"
    assert _extract_ip("[2001:db8::1]:8333") == "2001:db8::1"
    assert _extract_ip("invalid") is None


class DummyResolver:
    @property
    def is_configured(self) -> bool:
        return True

    def lookup(self, ip: str) -> dict[str, str | None]:
        if ip == "203.0.113.1":
            return {"country": "US", "asn": "AS64500 Example"}
        if ip == "198.51.100.5":
            return {"country": "CA", "asn": None}
        return {"country": None, "asn": None}


def test_create_peer_geo_points_counts_country_and_asn():
    config = CollectorConfig(bitcoin_network="mainnet")
    peers = [
        {"addr": "203.0.113.1:8333", "inbound": True},
        {"addr": "203.0.113.1:18333", "inbound": False},
        {"addr": "198.51.100.5:8333", "inbound": False},
    ]
    resolver = DummyResolver()

    points = create_peer_geo_points(config, peers, resolver)

    geo = {(
        point.tags["direction"],
        point.tags["country"],
    ): point.fields["peer_count"] for point in points if point.measurement == "peer_geo"}
    asn = {(
        point.tags["direction"],
        point.tags["asn"],
    ): point.fields["peer_count"] for point in points if point.measurement == "peer_asn"}

    assert geo[("inbound", "US")] == 1
    assert geo[("outbound", "US")] == 1
    assert geo[("outbound", "CA")] == 1
    assert asn[("inbound", "AS64500 Example")] == 1
    assert asn[("outbound", "AS64500 Example")] == 1
