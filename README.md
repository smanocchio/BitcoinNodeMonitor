# Bitcoin Node Monitoring Stack

An **easy-deploy** monitoring stack for **Bitcoin Core** node runners. One command brings up a Python collector, **InfluxDB v2**, **Grafana** dashboards, and optional **GeoIP** enrichment—tailored for home node operators.

> **Screenshots:** This repo is text-only (no binary assets). To capture your own, start the stack and in Grafana use **Share → Export → Download PNG** on the “01 Overview” dashboard (you can save it locally at `docs/images/overview-dashboard.png` if you like).

## Features
- **Collector → InfluxDB → Grafana** (no Prometheus endpoint)
- Blockchain sync & lag, mempool & fees, peer quality (geo/ASN), resource usage
- Optional **Electrs/Fulcrum** stats
- **Four prebuilt dashboards** (Overview, Sync & Health, Mempool & Fees, Peers & Geo)
- **Grafana-native alerting** (create rules in Grafana UI)
- Optional **GeoIP** enrichment via free MaxMind DBs (fetched at runtime)

## Requirements
- Docker Engine + Docker Compose Plugin (v2+)
- A running **Bitcoin Core** with RPC enabled (ZMQ optional but recommended)

## Quick Start (choose one)
### Option A — Bundled InfluxDB + Bundled Grafana (easiest)
```bash
cp .env.example .env
docker compose --profile bundled-influx --profile bundled-grafana up -d
Grafana: http://127.0.0.1:3000 (default admin/admin — change it!)

Option B — Existing InfluxDB, Bundled Grafana
bash
Copy code
cp .env.example .env
# Set INFLUX_URL, INFLUX_ORG, INFLUX_BUCKET, INFLUX_TOKEN in .env
USE_EXTERNAL_INFLUX=1 docker compose --profile bundled-grafana up -d
Option C — Existing InfluxDB + Existing Grafana
bash
Copy code
cp .env.example .env
# Set INFLUX_* and INFLUX_TOKEN in .env
USE_EXTERNAL_INFLUX=1 USE_EXTERNAL_GRAFANA=1 docker compose up -d collector
# In your Grafana, add an InfluxDB v2 (Flux) datasource and import grafana/dashboards/*.json
Bitcoin Core setup (important)
The collector pulls metrics from Bitcoin Core via RPC (and optionally ZMQ).
You do not point Bitcoin Core to a Prometheus or collector endpoint.

Minimal bitcoin.conf:

ini
Copy code
server=1
rpcbind=127.0.0.1
# If remote collector, allow your LAN and/or create a read-only RPC user:
# rpcallowip=192.168.0.0/16

# Optional (recommended):
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28333
Set matching envs in .env:

pgsql
Copy code
BITCOIN_RPC_HOST/PORT, BITCOIN_RPC_COOKIE_PATH (or USER/PASSWORD)
BITCOIN_ZMQ_RAWBLOCK, BITCOIN_ZMQ_RAWTX  (if you enabled ZMQ)
What you get after startup
Collector gathering metrics from Bitcoin Core RPC/ZMQ (+ optional Fulcrum/Electrs)

InfluxDB v2 with org/bucket/retention (bundled mode auto-provisions)

Grafana with datasource + pre-provisioned dashboards

Optional GeoIP enrichment (country/ASN counts only; no IPs stored)

Security defaults
Grafana & Influx bind to 127.0.0.1 by default.

Set EXPOSE_UI=1 to listen on all interfaces; if exposing, use a reverse proxy and change admin credentials.

No telemetry; use read-only RPC where possible.

GeoIP enrichment (optional, no binaries in git)
Get free MaxMind credentials and put them in .env:

ini
Copy code
GEOIP_ACCOUNT_ID=xxxx
GEOIP_LICENSE_KEY=yyyy
GEOIP_UPDATE_FREQUENCY_DAYS=7
Bring up the stack; the geoipupdate service fetches DBs into the mounted volume.

The collector uses country/ASN counts only (no IPs persisted).

Verify it’s working
bash
Copy code
docker compose ps
docker compose logs -f collector | head
# Grafana → Dashboards → “01 Overview” should show data within 1–2 minutes.
Grafana alerting (optional)
Create rules in Grafana UI:

Example: “Block lag > 2 for 5 minutes.”

Configure contact points (email, Slack, Telegram, etc.)

Common pitfalls
“.env not found” in CI: CI copies .env.example to .env before validation.

No data: verify RPC connectivity and INFLUX_* settings (if external).

ZMQ empty: confirm zmqpubrawblock/zmqpubrawtx and .env match.

External Influx perms: token needs bucket:write (collector) and read (Grafana).

Development
bash
Copy code
pip install -e .[dev]
ruff check .
mypy --config-file mypy.ini
pytest -q
Uninstall / clean up
bash
Copy code
docker compose down -v
License
MIT

(Optional) Prometheus note
Prefer Prometheus? Use a separate community exporter that talks to Core’s RPC and exposes /metrics for Prometheus. This repo ships InfluxDB + Grafana only.
