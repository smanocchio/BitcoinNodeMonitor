"""Collector entrypoint."""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
from typing import Dict, List

import requests
from requests import RequestException
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from .autodetect import find_cookie, format_cookie_auth
from .bitcoin_rpc import BitcoinRPC
from .config import CollectorConfig, load_config
from .fulcrum_client import FulcrumClient
from .geoip import GeoIPResolver
from .influx import InfluxWriter, Point
from .metrics import (
    FeeBucket,
    ReorgTracker,
    bucket_mempool_histogram,
    create_blockchain_points,
    create_mempool_points,
    create_peer_points,
    peers_metrics,
)
from .process_metrics import collect_disk_usage, collect_process_metrics
from .zmq_listener import ZMQListener

LOGGER = logging.getLogger(__name__)


def _build_rpc(config: CollectorConfig) -> BitcoinRPC:
    cookie = None
    if not config.bitcoin_rpc_user and not config.bitcoin_rpc_password:
        cookie_path = find_cookie(config.bitcoin_datadir)
        if cookie_path:
            cookie = format_cookie_auth(cookie_path)
    url = f"http://{config.bitcoin_rpc_host}:{config.bitcoin_rpc_port}"
    return BitcoinRPC(
        url=url,
        username=config.bitcoin_rpc_user,
        password=config.bitcoin_rpc_password,
        cookie=cookie,
    )


def _build_influx(config: CollectorConfig) -> InfluxWriter:
    token = config.influx_token or _read_token_file()
    return InfluxWriter(
        url=config.influx_url,
        token=token,
        org=config.influx_org,
        bucket=config.influx_bucket,
    )


def _read_token_file() -> str:
    try:
        with open("/var/lib/influxdb2/.influxdbv2/token", "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except FileNotFoundError:
        return ""


class CollectorService:
    def __init__(self, config: CollectorConfig) -> None:
        self.config = config
        self.rpc = _build_rpc(config)
        self.influx = _build_influx(config)
        self.reorg_tracker = ReorgTracker()
        self.zmq_listener = ZMQListener({
            "rawblock": config.bitcoin_zmq_rawblock,
            "rawtx": config.bitcoin_zmq_rawtx,
        })
        self.geoip = GeoIPResolver()
        self.fulcrum = FulcrumClient(config.fulcrum_stats_url)

    async def start(self) -> None:
        LOGGER.info("Starting ZMQ listener")
        self.zmq_listener.start()
        fast_task = asyncio.create_task(self._fast_loop())
        slow_task = asyncio.create_task(self._slow_loop())
        await asyncio.gather(fast_task, slow_task)

    async def _fast_loop(self) -> None:
        while True:
            start = time.time()
            try:
                await asyncio.to_thread(self.collect_fast)
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Fast loop error: %s", exc)
            elapsed = time.time() - start
            await asyncio.sleep(max(0, self.config.scrape_interval_fast - elapsed))

    async def _slow_loop(self) -> None:
        while True:
            start = time.time()
            try:
                await asyncio.to_thread(self.collect_slow)
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Slow loop error: %s", exc)
            elapsed = time.time() - start
            await asyncio.sleep(max(0, self.config.scrape_interval_slow - elapsed))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def collect_fast(self) -> None:
        LOGGER.debug("Collecting fast metrics")
        blockchain_info = self.rpc.get_blockchain_info()
        reorg_depth = self.reorg_tracker.update(blockchain_info.get("blocks", 0))
        points: List[Point] = []
        points.extend(
            create_blockchain_points(
                self.config,
                blockchain_info,
                reorg_depth,
                self.zmq_listener.status(),
            )
        )

        mempool_info = self.rpc.get_mempool_info()
        fee_estimates = {
            "fast": self._estimate_fee(3),
            "slow": self._estimate_fee(6),
        }
        points.extend(create_mempool_points(self.config, mempool_info, fee_estimates))

        hist_points = self._collect_mempool_histogram()
        points.extend(hist_points)

        self.influx.write_points(points)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def collect_slow(self) -> None:
        LOGGER.debug("Collecting slow metrics")
        peers = self.rpc.get_peer_info()
        summary = peers_metrics(peers)
        points: List[Point] = []
        points.extend(create_peer_points(self.config, summary))

        if self.config.enable_process_metrics:
            proc = collect_process_metrics()
            points.append(
                Point("process")
                .tag("name", "bitcoind")
                .field("cpu_percent", proc["cpu_percent"])
                .field("memory_rss_mb", proc["memory_rss_mb"])
                .field("open_files", proc["open_files"])
            )

        if self.config.enable_disk_io:
            disk = collect_disk_usage(self.config.bitcoin_chainstate_dir)
            points.append(
                Point("filesystem")
                .tag("path", self.config.bitcoin_chainstate_dir)
                .field("chainstate_gb", disk["used_gb"])
                .field("free_percent", disk["free_percent"])
            )

        try:
            fulcrum = self.fulcrum.fetch()
            points.append(
                Point("fulcrum")
                .field("tip_height", float(fulcrum.get("tip_height", 0)))
                .field("clients", float(fulcrum.get("clients", 0)))
            )
        except RequestException:
            LOGGER.debug("Fulcrum stats unavailable")

        self.influx.write_points(points)

    def _estimate_fee(self, blocks: int) -> float:
        try:
            result = self.rpc.estimatesmartfee(blocks)
            fee = result.get("feerate")
            return float(fee * 1e8 / 1000) if fee else 0.0
        except Exception:  # noqa: BLE001
            return 0.0

    def _collect_mempool_histogram(self) -> List[Point]:
        if self.config.mempool_hist_source == "none":
            return []
        hist: List[FeeBucket]
        if self.config.mempool_hist_source == "core_rawmempool":
            raw = self.rpc.get_raw_mempool(True)
            buckets: Dict[str, int] = {}
            for tx in raw.values():
                fee = tx.get("fees", {}).get("base", 0)
                vsize = tx.get("vsize", 1) or 1
                rate = (fee * 1e8) / vsize
                bucket_key = f"{int(rate // 5) * 5}-{int(rate // 5) * 5 + 5}"
                buckets[bucket_key] = buckets.get(bucket_key, 0) + 1
            hist = bucket_mempool_histogram(buckets)
        else:
            url = f"{self.config.mempool_api_base}/api/v1/fees/recommended"
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                hist = bucket_mempool_histogram(
                    {k: int(v) for k, v in data.items() if isinstance(v, (int, float))}
                )
            except requests.RequestException:
                hist = []
        points = []
        for entry in hist:
            point = Point("mempool_hist").tag("network", self.config.bitcoin_network)
            points.append(point.field(entry["bucket"], entry["count"]))
        return points

    def close(self) -> None:
        self.zmq_listener.stop()
        self.influx.close()
        self.geoip.close()


async def _run(config: CollectorConfig) -> None:
    service = CollectorService(config)
    try:
        await service.start()
    finally:
        service.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bitcoin Monitoring Collector")
    parser.add_argument("--healthcheck", action="store_true", help="Run healthcheck and exit")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = load_config()

    if args.healthcheck:
        LOGGER.info("Configuration loaded for %s", config.bitcoin_network)
        return

    try:
        asyncio.run(_run(config))
    except (KeyboardInterrupt, RetryError):
        LOGGER.info("Collector stopped")


if __name__ == "__main__":
    main()
