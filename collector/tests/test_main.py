from collector.config import CollectorConfig
from collector.main import _build_rpc


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
