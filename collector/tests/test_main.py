from types import SimpleNamespace

from collector.config import CollectorConfig
from collector.main import CollectorService, _build_rpc


class DummyRPC:
    def __init__(self, peers: list[dict]) -> None:
        self._peers = peers
        self.calls = 0

    def get_peer_info(self) -> list[dict]:
        self.calls += 1
        return self._peers


class DummyInflux:
    def __init__(self) -> None:
        self.writes: list[list] = []

    def write_points(self, points) -> None:
        self.writes.append(list(points))


def test_build_rpc_prefers_explicit_cookie(tmp_path, monkeypatch):
    cookie = tmp_path / "override.cookie"
    cookie.write_text("override-user:override-pass", encoding="utf-8")

    monkeypatch.setenv("BITCOIN_RPC_COOKIE_PATH", str(cookie))

    config = CollectorConfig()
    assert config.cookie_path == cookie

    def _fail_find_cookie(_):  # pragma: no cover - invoked only on regression
        raise AssertionError("_build_rpc should not inspect the datadir when a cookie override is set")

    monkeypatch.setattr("collector.main.find_cookie", _fail_find_cookie)

    rpc = _build_rpc(config)

    assert rpc.auth is not None
    assert rpc.auth.username == "override-user"
    assert rpc.auth.password == "override-pass"


def _build_service(monkeypatch, enable_peer_quality: bool) -> tuple[CollectorService, DummyRPC, DummyInflux]:
    peers = [
        {"inbound": True, "pingtime": 0.5},
        {"inbound": False, "pingtime": 0.25},
    ]
    fake_rpc = DummyRPC(peers)
    fake_influx = DummyInflux()
    monkeypatch.setattr("collector.main._build_rpc", lambda config: fake_rpc)
    monkeypatch.setattr("collector.main._build_influx", lambda config: fake_influx)
    config = CollectorConfig(
        enable_peer_quality=enable_peer_quality,
        enable_process_metrics=False,
        enable_disk_io=False,
    )
    service = CollectorService(config)
    service.fulcrum = SimpleNamespace(fetch=lambda: {})
    return service, fake_rpc, fake_influx


def test_collect_slow_writes_peers_when_enabled(monkeypatch):
    service, rpc, influx = _build_service(monkeypatch, enable_peer_quality=True)

    service.collect_slow()

    assert rpc.calls == 1
    assert influx.writes
    assert any(point.measurement == "peers" for point in influx.writes[0])


def test_collect_slow_skips_peers_when_disabled(monkeypatch):
    service, rpc, influx = _build_service(monkeypatch, enable_peer_quality=False)

    service.collect_slow()

    assert rpc.calls == 0
    assert influx.writes
    assert all(point.measurement != "peers" for point in influx.writes[0])
