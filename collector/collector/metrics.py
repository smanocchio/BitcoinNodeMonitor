"""Metric helpers for the collector."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol, Sequence, TypedDict

from .config import CollectorConfig
from .influx import Point


@dataclass
class ReorgTracker:
    """Track recent block heights to estimate reorg depth."""

    max_depth: int = 10
    history: List[int] = field(default_factory=list)

    def update(self, best_height: int) -> int:
        self.history.append(best_height)
        if len(self.history) > self.max_depth * 2:
            self.history = self.history[-self.max_depth * 2 :]
        return self.max_reorg_depth()

    def max_reorg_depth(self) -> int:
        if len(self.history) < 2:
            return 0
        diffs = [b - a for a, b in zip(self.history[:-1], self.history[1:], strict=False)]
        drops = [abs(diff) for diff in diffs if diff < 0]
        return max(drops) if drops else 0


def calculate_block_lag(headers: int, best: int) -> int:
    return max(headers - best, 0)


def percentile(values: Iterable[float], percent: float) -> float:
    data = sorted(v for v in values if v is not None)
    if not data:
        return 0.0
    k = (len(data) - 1) * percent
    f = int(k)
    c = min(f + 1, len(data) - 1)
    if f == c:
        return float(data[f])
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return float(d0 + d1)


class FeeBucket(TypedDict):
    bucket: str
    count: float


def bucket_mempool_histogram(raw: Mapping[str, int]) -> List[FeeBucket]:
    buckets: List[FeeBucket] = []
    for fee_range, count in raw.items():
        buckets.append({"bucket": fee_range, "count": float(count)})
    return buckets


def peers_metrics(peers: Sequence[Mapping[str, Any]]) -> Dict[str, float]:
    total = len(peers)
    inbound = len([p for p in peers if p.get("inbound")])
    outbound = total - inbound
    ping_values = [float(p.get("pingtime", 0.0) * 1000) for p in peers if p.get("pingtime")]
    return {
        "total": float(total),
        "inbound": float(inbound),
        "outbound": float(outbound),
        "ping_avg_ms": sum(ping_values) / len(ping_values) if ping_values else 0.0,
        "ping_p95_ms": percentile(ping_values, 0.95) if ping_values else 0.0,
    }


class GeoIPResolverProtocol(Protocol):
    def lookup(self, ip: str) -> Mapping[str, Optional[str]]:
        """Return GeoIP data for the supplied IP address."""


def _extract_peer_host(address: Optional[str]) -> Optional[str]:
    if not address:
        return None
    if address.startswith("["):
        end = address.find("]")
        if end > 0:
            return address[1:end]
        return None
    if ":" in address:
        host, _, port = address.rpartition(":")
        if host and port.isdigit():
            return host
    return address


def create_peer_geo_points(
    config: CollectorConfig,
    peers: Sequence[Mapping[str, Any]],
    resolver: GeoIPResolverProtocol,
) -> List[Point]:
    country_counts: Counter[str] = Counter()
    asn_counts: Counter[str] = Counter()

    for peer in peers:
        host = _extract_peer_host(peer.get("addr"))
        if not host:
            continue
        try:
            lookup = resolver.lookup(host)
        except Exception:  # noqa: BLE001
            continue
        if lookup is None:
            continue
        country = lookup.get("country")
        if country:
            country_counts[str(country)] += 1
        asn = lookup.get("asn")
        if asn:
            asn_counts[str(asn)] += 1

    points: List[Point] = []
    for country, count in country_counts.items():
        points.append(
            Point("peers_geo")
            .tag("network", config.bitcoin_network)
            .tag("country", country)
            .field("count", float(count))
        )
    for asn, count in asn_counts.items():
        points.append(
            Point("peers_asn")
            .tag("network", config.bitcoin_network)
            .tag("asn", asn)
            .field("count", float(count))
        )
    return points


def create_blockchain_points(
    config: CollectorConfig,
    blockchain_info: Mapping[str, Any],
    reorg_depth: int,
    zmq_status: Mapping[str, Mapping[str, Any]],
) -> List[Point]:
    points: List[Point] = []
    best_height = int(blockchain_info.get("blocks") or 0)
    headers = int(blockchain_info.get("headers") or best_height)
    lag = calculate_block_lag(headers, best_height)
    points.append(
        Point("blockchain")
        .tag("network", config.bitcoin_network)
        .field("best_height", float(best_height))
        .field("headers_height", float(headers))
        .field("block_lag", float(lag))
        .field("verification_progress", float(blockchain_info.get("verificationprogress", 0.0)))
        .field("difficulty", float(blockchain_info.get("difficulty", 0.0)))
        .field("max_reorg_depth", float(reorg_depth))
    )
    for topic, status in zmq_status.items():
        points.append(
            Point("zmq")
            .tag("stream", topic)
            .field("seconds_since", float(status.get("seconds_since", 0.0)))
            .field("messages", float(status.get("messages", 0.0)))
        )
    return points


def create_mempool_points(
    config: CollectorConfig,
    mempool_info: Mapping[str, Any],
    fee_estimates: Mapping[str, float],
) -> List[Point]:
    point = (
        Point("mempool")
        .tag("network", config.bitcoin_network)
        .field("tx_count", float(mempool_info.get("size", 0)))
        .field("vsize_mb", float((mempool_info.get("bytes", 0) or 0) / 1_000_000))
        .field("fee_fast", fee_estimates.get("fast", 0.0))
        .field("fee_slow", fee_estimates.get("slow", 0.0))
    )
    return [point]


def create_peer_points(config: CollectorConfig, summary: Mapping[str, float]) -> List[Point]:
    point = (
        Point("peers")
        .tag("network", config.bitcoin_network)
        .field("total", summary["total"])
        .field("inbound", summary["inbound"])
        .field("outbound", summary["outbound"])
        .field("ping_avg_ms", summary["ping_avg_ms"])
        .field("ping_p95_ms", summary["ping_p95_ms"])
    )
    return [point]
