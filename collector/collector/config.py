"""Configuration loader for the collector."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CollectorConfig(BaseSettings):
    """Pydantic-based configuration model."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    bitcoin_rpc_host: str = "127.0.0.1"
    bitcoin_rpc_port: int = 8332
    bitcoin_rpc_user: str = ""
    bitcoin_rpc_password: str = ""
    bitcoin_rpc_cookie_path: Optional[str] = "~/.bitcoin/.cookie"
    bitcoin_network: str = "mainnet"
    bitcoin_datadir: Optional[str] = "~/.bitcoin"
    bitcoin_chainstate_dir: Optional[str] = "~/.bitcoin/chainstate"

    bitcoin_zmq_rawblock: str = "tcp://127.0.0.1:28332"
    bitcoin_zmq_rawtx: str = "tcp://127.0.0.1:28333"

    fulcrum_stats_url: str = ""

    influx_url: str = "http://influxdb:8086"
    influx_org: str = "bitcoin"
    influx_bucket: str = "btc_metrics"
    influx_token: str = ""
    influx_tls_verify: bool = True

    scrape_interval_fast: int = 5
    scrape_interval_slow: int = 30

    enable_block_intervals: bool = True
    enable_softfork_signal: bool = True
    enable_peer_quality: bool = True
    enable_process_metrics: bool = True
    enable_disk_io: bool = True
    enable_peer_churn: bool = True
    enable_asn_stats: bool = True
    enable_zmq: bool = False

    mempool_hist_source: Literal["none", "core_rawmempool", "mempool_api"] = "none"
    mempool_api_base: str = "http://127.0.0.1:3006"

    geoip_account_id: str = ""
    geoip_license_key: str = ""
    geoip_update_frequency_days: int = 7

    collector_log_level: str = "INFO"

    @field_validator(
        "bitcoin_rpc_cookie_path",
        "bitcoin_datadir",
        "bitcoin_chainstate_dir",
        mode="before",
    )
    @classmethod
    def expand_user(cls, value: str | None) -> str | None:
        """Expand user home references (~) unless the value is blank."""

        if value is None:
            return None
        value_str = str(value).strip()
        if not value_str:
            return None
        return os.path.expanduser(value_str)

    @field_validator("mempool_hist_source", mode="before")
    @classmethod
    def validate_hist_source(cls, value: str | None) -> str:
        allowed = {"none", "core_rawmempool", "mempool_api"}
        if isinstance(value, str):
            value_str = value.strip().lower() or "none"
        else:
            value_str = str(value or "none").lower()
        if value_str not in allowed:
            raise ValueError(f"MEMPOOL_HIST_SOURCE must be one of {allowed}")
        return value_str

    @field_validator("influx_tls_verify", mode="before")
    @classmethod
    def normalize_influx_tls_verify(cls, value: object) -> bool | object:
        """Coerce common string and numeric values to booleans."""

        if isinstance(value, bool) or value is None:
            return value

        truthy = {"1", "true", "yes", "on"}
        falsy = {"0", "false", "no", "off"}

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in truthy:
                return True
            if normalized in falsy:
                return False
            raise ValueError(
                "INFLUX_TLS_VERIFY must be one of: 1, 0, true, false, yes, no, on, off"
            )

        if isinstance(value, int):
            if value in (0, 1):
                return bool(value)
            raise ValueError("INFLUX_TLS_VERIFY integer values must be 0 or 1")

        return value

    @field_validator("scrape_interval_fast", "scrape_interval_slow")
    @classmethod
    def positive_intervals(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Scrape intervals must be positive")
        return value

    @property
    def cookie_path(self) -> Optional[Path]:
        if not self.bitcoin_rpc_cookie_path:
            return None
        path = Path(self.bitcoin_rpc_cookie_path).expanduser()
        return path if path.exists() else None


def load_config() -> CollectorConfig:
    """Load configuration from environment variables."""

    return CollectorConfig()
