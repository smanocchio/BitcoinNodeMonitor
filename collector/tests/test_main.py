import logging
from types import SimpleNamespace

import pytest

from collector.config import CollectorConfig
from collector.main import CollectorService, _build_rpc, _read_token_file, _resolve_log_level


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
        raise AssertionError("_build_rpc must ignore the datadir when a cookie override is set")

    monkeypatch.setattr("collector.main.find_cookie", _fail_find_cookie)

    rpc = _build_rpc(config)

    assert rpc.auth is not None
    assert rpc.auth.username == "override-user"
    assert rpc.auth.password == "override-pass"


def test_build_rpc_skips_datadir_lookup_when_unset(monkeypatch, tmp_path):
    missing_cookie = tmp_path / "missing.cookie"

    def _fail_find_cookie(_):  # pragma: no cover - indicates regression
        raise AssertionError("find_cookie must not run when the datadir is unset")

    monkeypatch.setattr("collector.main.find_cookie", _fail_find_cookie)

    config = CollectorConfig(
        bitcoin_datadir=None,
        bitcoin_rpc_cookie_path=str(missing_cookie),
    )

    rpc = _build_rpc(config)

    assert rpc.auth is None


def _build_service(
    monkeypatch,
    *,
    enable_peer_quality: bool,
    enable_process_metrics: bool = False,
    enable_disk_io: bool = False,
    bitcoin_chainstate_dir: str | None = "~/.bitcoin/chainstate",
) -> tuple[CollectorService, DummyRPC, DummyInflux]:
    peers = [
        {"inbound": True, "pingtime": 0.5, "addr": "203.0.113.5:8333"},
        {"inbound": False, "pingtime": 0.25, "addr": "198.51.100.20:8333"},
    ]
    fake_rpc = DummyRPC(peers)
    fake_influx = DummyInflux()
    monkeypatch.setattr("collector.main._build_rpc", lambda config: fake_rpc)
    monkeypatch.setattr("collector.main._build_influx", lambda config: fake_influx)
    config = CollectorConfig(
        enable_peer_quality=enable_peer_quality,
        enable_process_metrics=enable_process_metrics,
        enable_disk_io=enable_disk_io,
        bitcoin_chainstate_dir=bitcoin_chainstate_dir,
    )
    service = CollectorService(config)
    service.fulcrum = SimpleNamespace(fetch=lambda: {})  # type: ignore[assignment]
    return service, fake_rpc, fake_influx


def test_collect_slow_writes_peers_when_enabled(monkeypatch):
    service, rpc, influx = _build_service(monkeypatch, enable_peer_quality=True)

    service.collect_slow()

    assert rpc.calls == 1
    assert influx.writes
    assert any(point.measurement == "peers" for point in influx.writes[0])


def test_collect_slow_enriches_geoip_when_enabled(monkeypatch):
    service, rpc, influx = _build_service(monkeypatch, enable_peer_quality=True)

    class DummyGeoIP:
        @property
        def is_configured(self) -> bool:
            return True

        def lookup(self, ip):
            return {"country": "US", "asn": "AS64500 Example"}

    service.geoip = DummyGeoIP()  # type: ignore[assignment]
    service.config.enable_asn_stats = True

    service.collect_slow()

    assert any(point.measurement == "peer_geo" for point in influx.writes[0])
    assert any(point.measurement == "peer_asn" for point in influx.writes[0])


def test_collect_slow_skips_peers_when_disabled(monkeypatch):
    service, rpc, influx = _build_service(monkeypatch, enable_peer_quality=False)

    service.collect_slow()

    assert rpc.calls == 0
    assert influx.writes
    assert all(point.measurement != "peers" for point in influx.writes[0])


def test_collect_slow_skips_filesystem_when_path_missing(monkeypatch):
    def _missing_disk_usage(path):
        raise FileNotFoundError(path)

    monkeypatch.setattr("collector.process_metrics.psutil.disk_usage", _missing_disk_usage)

    service, rpc, influx = _build_service(
        monkeypatch,
        enable_peer_quality=False,
        enable_disk_io=True,
        bitcoin_chainstate_dir="/nonexistent/path",
    )

    service.collect_slow()

    assert rpc.calls == 0
    assert influx.writes
    assert all(point.measurement != "filesystem" for point in influx.writes[0])


def test_collect_slow_skips_filesystem_when_path_disabled(monkeypatch):
    service, rpc, influx = _build_service(
        monkeypatch,
        enable_peer_quality=False,
        enable_disk_io=True,
        bitcoin_chainstate_dir=None,
    )

    service.collect_slow()

    assert rpc.calls == 0
    assert influx.writes
    assert all(point.measurement != "filesystem" for point in influx.writes[0])


def test_collect_slow_skips_process_metrics_when_process_missing(monkeypatch):
    monkeypatch.setattr("collector.main.collect_process_metrics", lambda: None)

    service, rpc, influx = _build_service(
        monkeypatch,
        enable_peer_quality=False,
        enable_process_metrics=True,
    )

    service.collect_slow()

    assert rpc.calls == 0
    assert influx.writes
    assert all(point.measurement != "process" for point in influx.writes[0])


def test_collect_slow_skips_fulcrum_when_url_blank(monkeypatch):
    service, rpc, influx = _build_service(monkeypatch, enable_peer_quality=False)
    service.fulcrum = None  # type: ignore[assignment]

    service.collect_slow()

    assert rpc.calls == 0
    assert influx.writes


def test_collect_slow_handles_nested_fulcrum_payload(monkeypatch):
    service, rpc, influx = _build_service(monkeypatch, enable_peer_quality=False)
    service.fulcrum = SimpleNamespace(
        fetch=lambda: {
            "daemon_height": 123,
            "clients": {"tcp": 2, "ssl": 3, "ws": "ignored"},
        }
    )

    service.collect_slow()

    assert rpc.calls == 0
    assert influx.writes
    fulcrum_points = [
        point for point in influx.writes[0] if point.measurement == "fulcrum"
    ]
    assert len(fulcrum_points) == 1
    point = fulcrum_points[0]
    assert point.fields["tip_height"] == 123.0
    assert point.fields["clients"] == 5.0


def test_resolve_log_level_is_case_insensitive():
    assert _resolve_log_level("debug") == logging.DEBUG
    assert _resolve_log_level(" Info ") == logging.INFO


def test_resolve_log_level_rejects_invalid_values():
    with pytest.raises(ValueError):
        _resolve_log_level("not-a-level")


def test_read_token_file_returns_empty_when_missing(monkeypatch):
    monkeypatch.setattr("builtins.open", open, raising=False)
    result = _read_token_file()
    assert result == ""


def test_read_token_file_uses_bootstrap_path(monkeypatch, tmp_path):
    token = tmp_path / "token"
    token.write_text("abc123", encoding="utf-8")

    original_open = open

    def fake_open(path, mode="r", encoding=None):
        if path == "/var/lib/influxdb2/.influxdbv2/token":
            return original_open(token, mode, encoding=encoding)
        return original_open(path, mode, encoding=encoding)

    monkeypatch.setattr("builtins.open", fake_open)

    assert _read_token_file() == "abc123"
