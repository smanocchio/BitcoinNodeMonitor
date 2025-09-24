"""Helpers to autodetect local Bitcoin Core resources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

BITCOIN_CONF_LOCATIONS = (
    Path("~/.bitcoin/bitcoin.conf"),
    Path("/etc/bitcoin/bitcoin.conf"),
)


def find_cookie(datadir: str | None) -> Optional[Path]:
    """Return the cookie path if it exists."""

    if not datadir:
        return None
    path = Path(datadir).expanduser() / ".cookie"
    return path if path.exists() else None


def read_bitcoin_conf(datadir: str | None = None) -> dict[str, str]:
    """Parse bitcoin.conf into a dictionary."""

    candidates = []
    if datadir:
        candidates.append(Path(datadir).expanduser() / "bitcoin.conf")
    candidates.extend(p.expanduser() for p in BITCOIN_CONF_LOCATIONS)

    for candidate in candidates:
        if candidate.exists():
            return _parse_conf(candidate)
    return {}


def _parse_conf(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def detect_rpc_credentials(datadir: str) -> Optional[tuple[str, str]]:
    """Attempt to read rpcauth credentials from bitcoin.conf."""

    conf = read_bitcoin_conf(datadir)
    user = conf.get("rpcuser")
    password = conf.get("rpcpassword")
    if user and password:
        return user, password
    return None


def format_cookie_auth(cookie_path: Path) -> tuple[str, str]:
    """Read the cookie file and extract username/password."""

    raw = cookie_path.read_text(encoding="utf-8").strip()
    if ":" in raw:
        username, password = raw.split(":", 1)
        return username, password
    raise ValueError("Malformed cookie file")


def describe_environment(config: dict[str, str]) -> str:
    """Return a JSON string summarizing detected configuration."""

    return json.dumps(config, indent=2, sort_keys=True)
