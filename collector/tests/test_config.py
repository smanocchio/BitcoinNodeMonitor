from collector.config import CollectorConfig


def test_defaults(tmp_path, monkeypatch):
    cookie = tmp_path / ".cookie"
    cookie.write_text("user:pass", encoding="utf-8")
    monkeypatch.setenv("BITCOIN_RPC_COOKIE_PATH", str(cookie))
    config = CollectorConfig()
    assert config.bitcoin_rpc_host == "127.0.0.1"
    assert config.cookie_path is not None
    assert config.enable_zmq is False


def test_invalid_hist_source(monkeypatch):
    monkeypatch.setenv("MEMPOOL_HIST_SOURCE", "invalid")
    try:
        CollectorConfig()
    except ValueError as exc:
        assert "MEMPOOL_HIST_SOURCE" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Config validation should have failed")


def test_enable_zmq_toggle(monkeypatch):
    monkeypatch.delenv("ENABLE_ZMQ", raising=False)
    config = CollectorConfig()
    assert config.enable_zmq is False

    monkeypatch.setenv("ENABLE_ZMQ", "1")
    config = CollectorConfig()
    assert config.enable_zmq is True
