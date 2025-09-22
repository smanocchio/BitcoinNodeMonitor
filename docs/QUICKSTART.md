# Quick Start Guide

This guide walks through installing and running the Bitcoin Monitoring Stack on Linux and Windows (via WSL). It assumes a running Bitcoin Core node reachable via RPC and (optionally) ZMQ.

## 1. Prerequisites

- Docker Engine 24+ and Docker Compose plugin (`docker compose`) installed.
- Bitcoin Core 25+ with RPC enabled (default on local nodes) and ZMQ notifiers configured if you want real-time metrics.
- Optional: MaxMind GeoLite2 account (free) for GeoIP enrichment.

## 2. Clone & Configure

```bash
git clone https://github.com/your-org/bitcoin-monitoring-stack.git
cd bitcoin-monitoring-stack
cp .env.example .env
```

Open `.env` in your editor and review the settings:

- For cookie authentication, leave `BITCOIN_RPC_USER`/`PASSWORD` empty and ensure `BITCOIN_RPC_COOKIE_PATH` points to your Bitcoin data directory.
- If using RPC username/password, set both values and clear `BITCOIN_RPC_COOKIE_PATH`.
- When running on Windows via WSL, use Linux-style paths (`/mnt/c/Users/...`).
- To enable GeoIP updates, set `GEOIP_ACCOUNT_ID` and `GEOIP_LICENSE_KEY` from MaxMind.

### Locating the `.cookie`

| OS | Default path |
|----|--------------|
| Linux | `~/.bitcoin/.cookie` |
| Windows (desktop Bitcoin Core) | `C:\\Users\\<name>\\AppData\\Roaming\\Bitcoin\\.cookie` |
| Umbrel/MyNode/Raspiblitz | Mount the external drive, find the `.cookie` inside the Bitcoin data directory |

If the collector runs on the same machine as Bitcoin Core, it autodetects the cookie path when left blank.

## 3. Start the Stack

```bash
docker compose up -d
```

The first run may take a few minutes while InfluxDB and Grafana initialize. Check logs with:

```bash
docker compose logs -f collector
```

## 4. Access Grafana

Visit [http://127.0.0.1:3000](http://127.0.0.1:3000) (default admin/admin credentials). Dashboards are pre-loaded under **Starred**.

If you need to access Grafana from your LAN:

1. In `.env`, set `EXPOSE_UI=1` and optionally update `GRAFANA_BIND_IP=0.0.0.0` and `INFLUX_BIND_IP=0.0.0.0` (see [Hardening](HARDENING.md) for security steps).
2. Re-run `docker compose up -d`.

## 5. Grafana Alerting Quickstart

1. In Grafana, go to **Alerts → Alert rules → New alert rule**.
2. Choose the **InfluxDB** datasource and select the relevant measurement (e.g., `block_lag`).
3. Build a query such as `max()` over the last 5 minutes.
4. Set the condition: `WHEN max() OF A IS ABOVE 2` for 5 minutes.
5. Add a contact point under **Alerts → Contact points** (email, Slack, Telegram, etc.).
6. Attach the contact point to the rule and save.

Example alert JSON for import is available at `grafana/dashboards/examples/alert_block_lag.json` (optional import via **Alerting → Alert rules → Migrate/Import**).

## 6. Windows (WSL) Notes

- Install Docker Desktop and enable the WSL backend.
- Place the repository inside your WSL home directory (`~/bitcoin-monitoring-stack`) for best performance.
- Use `/mnt/c/Users/<name>/AppData/Roaming/Bitcoin` for `BITCOIN_DATADIR` if Bitcoin Core runs on Windows.
- Map Windows paths into the collector container by editing the `BITCOIN_DATADIR` entry (e.g., `/mnt/c/Users/...`).

## 7. Stopping & Updating

```bash
docker compose down
# pull new images / update code
git pull
docker compose pull
docker compose up -d
```

## 8. Optional Components

- **Fulcrum/Electrs**: Set `FULCRUM_STATS_URL` to your server's stats endpoint to ingest tip height, clients, and resource usage.
- **Mempool Histogram**: Switch `MEMPOOL_HIST_SOURCE` to `core_rawmempool` (slower but self-contained) or `mempool_api` to use a local mempool.space API clone.

You're all set! Explore the dashboards and tune alerts to match your operational needs.
