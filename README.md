# BitcoinNodeMonitor

## Notes from previous nested README

The following documentation was preserved from the legacy `bitcoin-monitoring-stack/README.md` file to keep helpful deployment guidance accessible at the repository root.

### Legacy Overview

An easy-deploy monitoring stack for Bitcoin Core node runners. With a single command you can spin up a metrics collector, Influx DB 2.x, Grafana dashboards, and optional GeoIP enrichment tailored for home node operators.

> **Note:** Binary documentation assets (like PNG screenshots) are not stored in this repository. To view or capture the example Grafana dashboard screenshot referenced in the docs, start the stack and use Grafana's *Share → Export → Download PNG* feature on the "01 Overview" dashboard. Save the image as `docs/images/overview-dashboard.png` if you would like to keep a local copy.

### Legacy TL;DR Quick Start

```bash
cp .env.example .env
docker compose up -d
```

Within a couple of minutes you will have:

* **Collector** gathering metrics from Bitcoin Core via RPC and ZMQ, with optional Fulcrum/Electrs stats
* **InfluxDB** time-series database with a pre-created org, bucket, and retention
* **Grafana** dashboards and alerting pre-provisioned
* Optional **GeoIP** enrichment of peer locations using free MaxMind databases

### Legacy Contents

* Collector service written in Python (FastAPI + Prometheus exporters)
* Pre-built dashboards for node health, mempool activity, and network peers
* InfluxDB with bucket retention and Telegraf output templates
* Grafana provisioning for dashboards, data sources, and alert notification channels

### Legacy Requirements

* Docker Engine and Docker Compose Plugin (v2+)
* Bitcoin Core node with RPC enabled

### Legacy Deployment Steps

1. Copy `.env.example` to `.env` and fill in required values like `BITCOIN_RPC_USER` and `BITCOIN_RPC_PASSWORD`.
2. Optionally adjust ports, data paths, and retention policies in `docker-compose.yml`.
3. Run `docker compose up -d` to start all services.
4. Access Grafana at http://localhost:3000 (default credentials: admin/admin).
5. Point your Bitcoin Core node's `prometheus` option to the collector's metrics endpoint (`collector:9333`).

### Legacy GeoIP Enrichment (Optional)

If you want to enrich peer IP addresses with GeoIP data:

1. Obtain free MaxMind GeoLite2-City and GeoLite2-ASN databases.
2. Place the `.mmdb` files in `geoip/` and set `ENABLE_GEOIP=true` in your `.env`.
3. Restart the stack.

### Legacy Development Notes

* `collector/` contains a FastAPI app that can be run locally via `uvicorn collector.main:app --reload`.
* Tests use `pytest`; run `pytest` from the `collector/` directory.
* `ruff` and `mypy` help maintain code quality.

### Legacy Troubleshooting Tips

* See `docs/TROUBLESHOOTING.md` for common issues and solutions.
* For configuration details, check `docs/CONFIG.md` and `docs/HARDENING.md`.
