# Bitcoin Node Monitoring Stack

An **easy-deploy** monitoring stack for **Bitcoin Core** node runners. One command brings up a Python collector, **InfluxDB v2**, **Grafana** dashboards, and optional **GeoIP** enrichment—tailored for home node operators.

---

## Table of Contents
- [What You Get](#what-you-get)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
  - [Option A — Bundled InfluxDB + Bundled Grafana](#option-a--bundled-influxdb--bundled-grafana)
  - [Option B — Existing InfluxDB, Bundled Grafana](#option-b--existing-influxdb-bundled-grafana)
  - [Option C — Existing InfluxDB + Existing Grafana](#option-c--existing-influxdb--existing-grafana)
- [Bitcoin Core Setup](#bitcoin-core-setup)
- [Configuration Cheatsheet](#configuration-cheatsheet)
- [Security Defaults](#security-defaults)
- [GeoIP Enrichment (Optional)](#geoip-enrichment-optional)
- [Verify It’s Working](#verify-its-working)
- [Grafana Alerting (Optional)](#grafana-alerting-optional)
- [Common Pitfalls](#common-pitfalls)
- [Uninstall / Clean Up](#uninstall--clean-up)
- [License](#license)
- [Prometheus Note](#prometheus-note)

---

## What You Get
- **Collector → InfluxDB → Grafana** (no Prometheus endpoint)
- Blockchain sync & lag, mempool & fees, peer quality (geo/ASN), resource usage
- Optional **Electrs/Fulcrum** `/stats` metrics
- **Four prebuilt dashboards** (Overview, Sync & Health, Mempool & Fees, Peers & Geo)
- **Grafana-native alerting** (create alert rules in Grafana UI)
- Optional **GeoIP** enrichment via free MaxMind DBs (fetched at runtime; no IPs persisted—only country/ASN counts)

---

## How It Works

```
+----------------+   RPC (+optional ZMQ)   +-----------+
|  Bitcoin Core  | <--------------------- | Collector |
|   (bitcoind)   |                        | (Python)  |
+----------------+                        +-----------+
          | Influx line protocol
          v
    +-----------+
    | InfluxDB  |
    |    v2     |
    +-----------+
          | Flux queries
          v
    +-----------+
    | Grafana   |
    | Dashboards|
    |  Alerting |
    +-----------+
```

---

## Requirements
- Docker Engine + Docker Compose Plugin (v2)
- A running **Bitcoin Core** with RPC enabled (ZMQ optional but recommended)

---

## Quick Start

### Option A — Bundled InfluxDB + Bundled Grafana (easiest)
```bash
cp .env.example .env
docker compose --profile bundled-influx --profile bundled-grafana up -d
```
Open Grafana at <http://127.0.0.1:3000> (default `admin`/`admin` — change it!).

### Option B — Existing InfluxDB, Bundled Grafana
```bash
cp .env.example .env
# Set these in .env before starting:
#   INFLUX_URL, INFLUX_ORG, INFLUX_BUCKET, INFLUX_TOKEN
USE_EXTERNAL_INFLUX=1 docker compose --profile bundled-grafana up -d
```

### Option C — Existing InfluxDB + Existing Grafana
```bash
cp .env.example .env
# Set INFLUX_URL, INFLUX_ORG, INFLUX_BUCKET, INFLUX_TOKEN in .env
USE_EXTERNAL_INFLUX=1 USE_EXTERNAL_GRAFANA=1 docker compose up -d collector
```
In your external Grafana, add an **InfluxDB v2 (Flux)** datasource, then import `grafana/dashboards/*.json`.

> **Tip:** If your Compose file ignores profiles, `docker compose up -d` starts the bundled stack.

---

## Bitcoin Core Setup
The collector pulls metrics from Bitcoin Core via RPC (and optionally ZMQ). You do **not** point Bitcoin Core to this stack.

Minimal `bitcoin.conf`:

```ini
server=1
rpcbind=127.0.0.1
# If the collector runs on another host, allow your LAN and/or create a read-only RPC user:
# rpcallowip=192.168.0.0/16

# Optional (recommended) for richer metrics:
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28333
```

Match these in `.env`:

```
BITCOIN_RPC_HOST / BITCOIN_RPC_PORT
BITCOIN_RPC_COOKIE_PATH (or BITCOIN_RPC_USER / BITCOIN_RPC_PASSWORD)
BITCOIN_ZMQ_RAWBLOCK / BITCOIN_ZMQ_RAWTX (if enabling ZMQ)
```

---

## Configuration Cheatsheet
Minimal edits in `.env` (same-box cookie auth):

```
BITCOIN_RPC_COOKIE_PATH=~/.bitcoin/.cookie
```

If using external InfluxDB:

```
INFLUX_URL
INFLUX_ORG
INFLUX_BUCKET
INFLUX_TOKEN
```

Retention (bundled InfluxDB only):

```
INFLUX_RETENTION_DAYS=60  # set to your preference
```

LAN access to UIs (off by default):

```
EXPOSE_UI=1  # then front with a reverse proxy
```

Feature flags (examples):

```ini
ENABLE_BLOCK_INTERVALS=1
ENABLE_PEER_QUALITY=1
ENABLE_PROCESS_METRICS=1
ENABLE_DISK_IO=1
ENABLE_PEER_CHURN=1
ENABLE_ASN_STATS=1
MEMPOOL_HIST_SOURCE=none   # or core_rawmempool | mempool_api
```

Electrum indexer metrics:

```
ELECTRS_STATS_URL=http://127.0.0.1:4224/stats
FULCRUM_STATS_URL=http://127.0.0.1:8080/stats
```

---

## Security Defaults
- Grafana & Influx bind to `127.0.0.1` by default.
- Set `EXPOSE_UI=1` to listen on all interfaces; if exposing to LAN/Internet, put behind a reverse proxy and change default credentials.
- No telemetry; the collector never phones home. Prefer a read-only RPC user when not using cookie auth.

---

## GeoIP Enrichment (Optional)
This repo does **not** commit `.mmdb` files. A sidecar fetches them at runtime.

1. Get free MaxMind credentials.
2. In `.env` set:
   ```ini
   GEOIP_ACCOUNT_ID=xxxx
   GEOIP_LICENSE_KEY=yyyy
   GEOIP_UPDATE_FREQUENCY_DAYS=7
   ```
3. Start the stack. The `geoipupdate` service downloads the databases into the mounted volume.

The collector uses country/ASN counts only (no IPs are persisted).

---

## Verify It’s Working
```bash
docker compose ps
docker compose logs -f collector | head
```
Then in Grafana open **Dashboards → “01 Overview”** and confirm data within 1–2 minutes.

---

## Grafana Alerting (Optional)
Use Grafana’s native alerting:

1. Grafana → **Alerting → Alert rules → New alert rule**.
2. Example: “Block lag > 2 for 5 minutes”.
3. Configure **Contact points** (email, Slack, Telegram, etc.).

---

## Common Pitfalls
- “`.env` not found” in CI: copy `.env.example` to `.env` before validation.
- No data in dashboards: verify RPC connectivity and `INFLUX_*` settings (if external).
- ZMQ panels empty: confirm `zmqpubrawblock` / `zmqpubrawtx` match `.env` values.
- External Influx perms: token needs `bucket:write` (collector) and read for Grafana.

---

## Uninstall / Clean Up
```bash
docker compose down -v
```

---

## License
MIT

---

## Prometheus Note
This stack does **not** expose a Prometheus endpoint or port 9333. All metrics flow Collector → InfluxDB → Grafana.
