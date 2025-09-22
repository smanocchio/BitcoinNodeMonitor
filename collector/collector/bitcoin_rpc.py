"""Minimal Bitcoin Core RPC client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth


@dataclass
class RPCError(Exception):
    code: int
    message: str

    def __str__(self) -> str:  # noqa: D401
        return f"RPC error {self.code}: {self.message}"


class BitcoinRPC:
    """Lightweight JSON-RPC client with cookie or user/password auth."""

    def __init__(
        self,
        url: str,
        username: str = "",
        password: str = "",
        cookie: Optional[tuple[str, str]] = None,
        timeout: int = 10,
    ) -> None:
        self.url = url
        self.timeout = timeout
        if cookie:
            username, password = cookie
        self.auth = HTTPBasicAuth(username, password) if username or password else None

    def call(self, method: str, *params: Any) -> Any:
        payload = {"jsonrpc": "2.0", "id": "btc-monitor", "method": method, "params": list(params)}
        response = requests.post(
            self.url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            auth=self.auth,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        if data.get("error"):
            error = data["error"]
            raise RPCError(code=error.get("code", -1), message=error.get("message", "Unknown"))
        return data.get("result")

    # Convenience wrappers -------------------------------------------------

    def get_blockchain_info(self) -> Dict[str, Any]:
        return self.call("getblockchaininfo")

    def get_mempool_info(self) -> Dict[str, Any]:
        return self.call("getmempoolinfo")

    def get_network_info(self) -> Dict[str, Any]:
        return self.call("getnetworkinfo")

    def get_peer_info(self) -> list[Dict[str, Any]]:
        return self.call("getpeerinfo")

    def get_mining_info(self) -> Dict[str, Any]:
        return self.call("getmininginfo")

    def get_raw_mempool(self, verbose: bool = True) -> Dict[str, Any]:
        return self.call("getrawmempool", verbose)

    def estimatesmartfee(self, blocks: int) -> Dict[str, Any]:
        return self.call("estimatesmartfee", blocks)
