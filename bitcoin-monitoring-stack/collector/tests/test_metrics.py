from collector.metrics import (
    ReorgTracker,
    bucket_mempool_histogram,
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
