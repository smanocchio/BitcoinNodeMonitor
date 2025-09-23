import json

import pytest
import requests
from requests import Response

from collector.bitcoin_rpc import BitcoinRPC, RPCError


class DummyResponse(Response):
    def __init__(self, status_code: int, payload: dict) -> None:
        super().__init__()
        self.status_code = status_code
        self._content = json.dumps(payload).encode()


def test_call_raises_rpc_error(monkeypatch):
    rpc = BitcoinRPC("http://localhost:8332")

    def fake_post(*args, **kwargs):
        payload = {
            "jsonrpc": "2.0",
            "id": "btc-monitor",
            "error": {"code": -8, "message": "Unknown block"},
        }
        return DummyResponse(200, payload)

    monkeypatch.setattr("collector.bitcoin_rpc.requests.post", fake_post)

    with pytest.raises(RPCError) as excinfo:
        rpc.call("getblock")

    assert excinfo.value.code == -8
    assert "Unknown block" in str(excinfo.value)


def test_call_propagates_request_exception(monkeypatch):
    rpc = BitcoinRPC("http://localhost:8332")

    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("connection failed")

    monkeypatch.setattr("collector.bitcoin_rpc.requests.post", fake_post)

    with pytest.raises(requests.ConnectionError):
        rpc.call("getblockchaininfo")
