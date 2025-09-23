# Configuration Reference

The collector relies on environment variables that are loaded into the `CollectorConfig`
model. Docker Compose uses the same variables to configure InfluxDB, Grafana, and GeoIP
services. This document explains every option and how they interact.

## Configuration Layers

1. **`.env` file** – optional file read by Docker Compose and `pydantic-settings`. Copy
   `.env.example` and adjust it for your deployment.
2. **Environment variables** – overrides passed at runtime take precedence over values in
   `.env`.
3. **Defaults** – baked into `collector/config.py` and reflect sensible mainnet settings.

## Bitcoin Core Connectivity

| Variable | Default | Description |
|----------|---------|-------------|
| `BITCOIN_RPC_HOST` | `127.0.0.1` | Hostname/IP for the JSON-RPC endpoint. |
| `BITCOIN_RPC_PORT` | `8332` | RPC port. Adjust for testnet/regtest. |
| `BITCOIN_RPC_USER` / `BITCOIN_RPC_PASSWORD` | _empty_ | Explicit RPC credentials. Leave blank when using cookie auth. |
| `BITCOIN_RPC_COOKIE_PATH` | `~/.bitcoin/.cookie` | Fallback cookie location. The collector also searches inside the mounted data directory. |
| `BITCOIN_NETWORK` | `mainnet` | Tag applied to every metric. Supports custom values such as `testnet` or `signet`. |
| `BITCOIN_DATADIR` | `~/.bitcoin` | Mounted into the collector container to access the cookie file and configuration. |
| `BITCOIN_CHAINSTATE_DIR` | `~/.bitcoin/chainstate` | Used when disk utilisation metrics are enabled. |
| `ENABLE_DISK_IO` | `1` | Samples disk usage for the chainstate directory. |
| `ENABLE_ZMQ` | `0` | Set to `1` to collect ZMQ freshness metrics. Leave at `0` when you do not need the Grafana ZMQ panels. |
| `BITCOIN_ZMQ_RAWBLOCK` | `tcp://127.0.0.1:28332` | Endpoint for raw block notifications. Must match `bitcoin.conf` when ZMQ metrics are enabled. |
| `BITCOIN_ZMQ_RAWTX` | `tcp://127.0.0.1:28333` | Endpoint for raw transaction notifications. Must match `bitcoin.conf` when ZMQ metrics are enabled. |
| `FULCRUM_STATS_URL` | `http://127.0.0.1:8080/stats` | Optional Fulcrum/Electrs stats endpoint. Leave empty to disable. |

The collector automatically reads the cookie file when both username and password are empty.
If the cookie cannot be found, make sure the data directory is mounted read-only into the
container (see `docker-compose.yml`). Disk utilisation sampling also relies on the
chainstate directory being available; disable `ENABLE_DISK_IO` when the path is not
mounted. When ZMQ metrics remain disabled the collector skips starting the listener and
simply omits the corresponding measurements.

## InfluxDB Options

| Variable | Default | Purpose |
|----------|---------|---------|
| `INFLUX_URL` | `http://influxdb:8086` | Base URL for the InfluxDB API. Point to an external instance to reuse existing infrastructure. |
| `INFLUX_ORG` | `bitcoin` | Organisation created during bootstrap and used by Grafana. |
| `INFLUX_BUCKET` | `btc_metrics` | Bucket name that stores metrics. |
| `INFLUX_RETENTION_DAYS` | `60` | Retention period applied during bootstrap. |
| `INFLUX_SETUP_USERNAME` / `INFLUX_SETUP_PASSWORD` | `admin` / `admin123` | Credentials used once during bootstrap to create the initial API token. |
| `INFLUX_TOKEN` | _empty_ | If provided, overrides the generated token and is used by both the collector and Grafana. |
| `INFLUX_BIND_IP` | `127.0.0.1` | Bind address used when exposing the InfluxDB UI through Docker Compose port mapping. |
| `USE_EXTERNAL_INFLUX` | `0` | Set to `1` to skip starting the bundled InfluxDB service. |

The bootstrap script writes the active token to `/var/lib/influxdb2/.influxdbv2/token`. The
collector reads the file when `INFLUX_TOKEN` is empty.

## Grafana Options

| Variable | Default | Purpose |
|----------|---------|---------|
| `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` | `admin` / `admin` | Initial administrator credentials. |
| `GRAFANA_BIND_IP` | `127.0.0.1` | Bind address for the HTTP server. Combine with `EXPOSE_UI=1` to listen beyond localhost. |
| `EXPOSE_UI` | `0` | When set to `1`, Docker Compose binds Grafana to all interfaces. See hardening guidance before exposing externally. |
| `USE_EXTERNAL_GRAFANA` | `0` | Set to `1` to skip the bundled Grafana container. |

Grafana provisioning picks up the same InfluxDB credentials that the collector uses, so
changes to `INFLUX_*` variables should be reflected here as well.

## Collector Behaviour Flags

| Variable | Default | Effect |
|----------|---------|--------|
| `SCRAPE_INTERVAL_FAST` | `5` | Seconds between fast loop executions. |
| `SCRAPE_INTERVAL_SLOW` | `30` | Seconds between slow loop executions. |
| `ENABLE_BLOCK_INTERVALS` | `1` | Placeholder flag for enabling additional block cadence analytics. |
| `ENABLE_SOFTFORK_SIGNAL` | `1` | Placeholder flag for signalling dashboards. |
| `ENABLE_PEER_QUALITY` | `1` | Enables peer latency aggregations. |
| `ENABLE_PROCESS_METRICS` | `1` | Collects CPU, memory, and file descriptor counts for the `bitcoind` process using `psutil`. |
| `ENABLE_PEER_CHURN` | `1` | Reserved for future peer churn calculations. |

Flags marked as placeholders do not currently toggle additional logic but are included for
future compatibility with dashboards.

## Mempool Histogram Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMPOOL_HIST_SOURCE` | `none` | `core_rawmempool` performs a full verbose `getrawmempool` pull every fast scrape, rolls the results into 5-sat/vbyte buckets, and writes a `mempool_hist` measurement at the cost of extra RPC, CPU, and network overhead. `mempool_api` fetches `/api/v1/fees/recommended` from `MEMPOOL_API_BASE`, expects a JSON object of bucket names mapped to numeric counts, converts each entry into histogram buckets, and skips the cycle when the request fails. |
| `MEMPOOL_API_BASE` | `http://127.0.0.1:3006` | Base URL for the external API when `MEMPOOL_HIST_SOURCE=mempool_api`. The collector appends `/api/v1/fees/recommended`. |

Choose `core_rawmempool` when you control the node and want the Grafana “Mempool Fee Histogram” panel to reflect precise 5-sat/vbyte buckets, accepting the additional RPC and processing load. Use `mempool_api` to delegate the histogram counts to an external service (with transient failures simply omitting an update) or stick with `none` to disable the panel entirely.

When histogram collection is disabled (`none`), the collector skips external calls and no
`mempool_hist` measurement is written.

## GeoIP Update Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `GEOIP_ACCOUNT_ID` / `GEOIP_LICENSE_KEY` | _empty_ | MaxMind account credentials required to download GeoLite2 databases. |
| `GEOIP_UPDATE_FREQUENCY_DAYS` | `7` | How often `geoipupdate` refreshes the databases. |
| `ENABLE_ASN_STATS` | `1` | Enables ASN lookup fields when GeoIP data is available. |

If credentials are omitted the update container will fail gracefully; peer metrics will still
collect counts but without country/ASN enrichment. Toggle `ENABLE_ASN_STATS` off when you
prefer to skip ASN lookups altogether.

## Customising for Testnet or Signet

* Set `BITCOIN_NETWORK` to the desired name for tagging.
* Override `BITCOIN_RPC_PORT` (e.g. `18332` for testnet) and adjust ZMQ ports as configured
  in `bitcoin.conf`.
* Consider reducing retention or adjusting scrape intervals for small nodes.

With these options you can tailor the monitoring stack for home nodes, staging environments,
or production deployments.
