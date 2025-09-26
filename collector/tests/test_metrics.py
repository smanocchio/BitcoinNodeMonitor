from decimal import Decimal

from collector.config import CollectorConfig
from collector.metrics import (
    ReorgTracker,
    _extract_ip,
    bucket_mempool_histogram,
    create_peer_geo_points,
    peers_metrics,
    percentile,
)


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

    def lookup(self, ip: str) -> dict[str, str | float | None]:
        if ip == "203.0.113.1":
            return {
                "country": "US",
                "asn": "AS64500 Example",
                "latitude": 37.7749,
                "longitude": -122.4194,
            }
        if ip == "198.51.100.5":
            return {
                "country": "CA",
                "asn": None,
                "latitude": 45.4215,
                "longitude": -75.6972,
            }
        return {"country": None, "asn": None, "latitude": None, "longitude": None}


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


def test_create_peer_geo_points_includes_coordinates():
    config = CollectorConfig(bitcoin_network="mainnet")
    peers = [
        {"addr": "203.0.113.1:8333", "inbound": True},
        {"addr": "198.51.100.5:8333", "inbound": False},
    ]
    resolver = DummyResolver()

    points = create_peer_geo_points(config, peers, resolver)

    coord_points = [
        point for point in points if point.measurement == "peer_geo_coords"
    ]

    assert len(coord_points) == 2

    inbound_point = next(
        point for point in coord_points if point.tags["direction"] == "inbound"
    )
    assert inbound_point.fields["latitude"] == 37.7749
    assert inbound_point.fields["longitude"] == -122.4194
    assert inbound_point.tags["ip"] == "203.0.113.1"
    assert inbound_point.tags["country"] == "US"
    assert inbound_point.tags["asn"] == "AS64500 Example"

    outbound_point = next(
        point for point in coord_points if point.tags["direction"] == "outbound"
    )
    assert outbound_point.fields["latitude"] == 45.4215
    assert outbound_point.fields["longitude"] == -75.6972
    assert outbound_point.tags["ip"] == "198.51.100.5"
    assert outbound_point.tags["country"] == "CA"


class DecimalResolver:
    @property
    def is_configured(self) -> bool:
        return True

    def lookup(self, ip: str) -> dict[str, str | float | Decimal | None]:
        return {
            "country": "US",
            "asn": "AS64500 Example",
            "latitude": Decimal("37.7749"),
            "longitude": Decimal("-122.4194"),
        }


def test_create_peer_geo_points_accepts_decimal_coordinates():
    config = CollectorConfig(bitcoin_network="mainnet")
    peers = [{"addr": "203.0.113.1:8333", "inbound": True}]
    resolver = DecimalResolver()

    points = create_peer_geo_points(config, peers, resolver)

    coord_points = [
        point for point in points if point.measurement == "peer_geo_coords"
    ]

    assert len(coord_points) == 1
    coord_point = coord_points[0]
    assert isinstance(coord_point.fields["latitude"], float)
    assert isinstance(coord_point.fields["longitude"], float)
    assert coord_point.fields["latitude"] == float(Decimal("37.7749"))
    assert coord_point.fields["longitude"] == float(Decimal("-122.4194"))
