"""Configuration loader for the collector."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - prefer real pydantic when available
    from pydantic import BaseSettings, Field, validator
except ImportError:  # pragma: no cover
    from .pydantic_stub import BaseSettings, Field, validator


class CollectorConfig(BaseSettings):
    """Pydantic-based configuration model."""

    bitcoin_rpc_host: str = Field("127.0.0.1", env="BITCOIN_RPC_HOST")
    bitcoin_rpc_port: int = Field(8332, env="BITCOIN_RPC_PORT")
    bitcoin_rpc_user: str = Field("", env="BITCOIN_RPC_USER")
    bitcoin_rpc_password: str = Field("", env="BITCOIN_RPC_PASSWORD")
    bitcoin_rpc_cookie_path: str = Field("~/.bitcoin/.cookie", env="BITCOIN_RPC_COOKIE_PATH")
    bitcoin_network: str = Field("mainnet", env="BITCOIN_NETWORK")
    bitcoin_datadir: str = Field("~/.bitcoin", env="BITCOIN_DATADIR")
    bitcoin_chainstate_dir: str = Field("~/.bitcoin/chainstate", env="BITCOIN_CHAINSTATE_DIR")

    bitcoin_zmq_rawblock: str = Field("tcp://127.0.0.1:28332", env="BITCOIN_ZMQ_RAWBLOCK")
    bitcoin_zmq_rawtx: str = Field("tcp://127.0.0.1:28333", env="BITCOIN_ZMQ_RAWTX")

    fulcrum_stats_url: str = Field("http://127.0.0.1:8080/stats", env="FULCRUM_STATS_URL")

    influx_url: str = Field("http://influxdb:8086", env="INFLUX_URL")
    influx_org: str = Field("bitcoin", env="INFLUX_ORG")
    influx_bucket: str = Field("btc_metrics", env="INFLUX_BUCKET")
    influx_token: str = Field("", env="INFLUX_TOKEN")

    scrape_interval_fast: int = Field(5, env="SCRAPE_INTERVAL_FAST")
    scrape_interval_slow: int = Field(30, env="SCRAPE_INTERVAL_SLOW")

    enable_block_intervals: bool = Field(True, env="ENABLE_BLOCK_INTERVALS")
    enable_softfork_signal: bool = Field(True, env="ENABLE_SOFTFORK_SIGNAL")
    enable_peer_quality: bool = Field(True, env="ENABLE_PEER_QUALITY")
    enable_process_metrics: bool = Field(True, env="ENABLE_PROCESS_METRICS")
    enable_disk_io: bool = Field(True, env="ENABLE_DISK_IO")
    enable_peer_churn: bool = Field(True, env="ENABLE_PEER_CHURN")
    enable_asn_stats: bool = Field(True, env="ENABLE_ASN_STATS")

    mempool_hist_source: str = Field("none", env="MEMPOOL_HIST_SOURCE")
    mempool_api_base: str = Field("http://127.0.0.1:3006", env="MEMPOOL_API_BASE")

    geoip_account_id: str = Field("", env="GEOIP_ACCOUNT_ID")
    geoip_license_key: str = Field("", env="GEOIP_LICENSE_KEY")
    geoip_update_frequency_days: int = Field(7, env="GEOIP_UPDATE_FREQUENCY_DAYS")

    collector_log_level: str = Field("INFO", env="COLLECTOR_LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("bitcoin_rpc_cookie_path", "bitcoin_datadir", "bitcoin_chainstate_dir", pre=True)
    def expand_user(cls, value: str) -> str:  # noqa: D401
        """Expand user home references (~)."""

        return os.path.expanduser(value)

    @validator("mempool_hist_source")
    def validate_hist_source(cls, value: str) -> str:
        allowed = {"none", "core_rawmempool", "mempool_api"}
        if value not in allowed:
            raise ValueError(f"MEMPOOL_HIST_SOURCE must be one of {allowed}")
        return value

    @validator("scrape_interval_fast", "scrape_interval_slow")
    def positive_intervals(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Scrape intervals must be positive")
        return value

    @property
    def cookie_path(self) -> Optional[Path]:
        path = Path(self.bitcoin_rpc_cookie_path).expanduser()
        return path if path.exists() else None


def load_config() -> CollectorConfig:
    """Load configuration from environment variables."""

    return CollectorConfig()
