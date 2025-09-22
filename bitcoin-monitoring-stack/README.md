# Bitcoin Monitoring Stack

An easy-deploy monitoring stack for Bitcoin Core node runners. With a single command you can spin up a metrics collector, InfluxDB 2.x, Grafana dashboards, and optional GeoIP enrichment tailored for home node operators.

> **Note:** Binary documentation assets (like PNG screenshots) are not stored in this repository. To view or capture the example
> Grafana dashboard screenshot referenced in the docs, start the stack and use Grafana's *Share → Export → Download PNG* feature
> on the "01 Overview" dashboard. Save the image as `docs/images/overview-dashboard.png` if you would like to keep a local copy.

## TL;DR Quick Start

```bash
cp .env.example .env
docker compose up -d
```

Within a couple of minutes you will have:

* **Collector** gathering metrics from Bitcoin Core via RPC and ZMQ, with optional Fulcrum/Electrs stats
* **InfluxDB** time-series database with a pre-created org, bucket, and retention
* **Grafana** dashboards and alerting pre-provisioned
* **GeoIP updater** fetching country/ASN metadata (optional)

> **Security warning:** All web services bind to `127.0.0.1` by default. If you expose Grafana or InfluxDB to your LAN or the internet, follow the hardening guidance in [`docs/HARDENING.md`](docs/HARDENING.md).

## What's Included

* Python 3.11 collector with autodetection of local cookie auth, retry/backoff, and modular metric harvesting
* Docker Compose deployment tested on Linux and Windows (via WSL)
* Grafana dashboards covering node health, sync status, mempool fees, peer geography/ASN, and resource usage
* Documentation for setup, configuration, troubleshooting, hardening, and architecture overview
* GitHub Actions CI for linting, typing, testing, and docker compose validation

## Documentation

* [Quick Start](docs/QUICKSTART.md) – step-by-step install for Linux & Windows
* [Configuration](docs/CONFIG.md) – environment variables and feature flags
* [Troubleshooting](docs/TROUBLESHOOTING.md) – common issues and fixes
* [Hardening](docs/HARDENING.md) – secure exposure, reverse proxy samples, Grafana hardening
* [Architecture](docs/ARCHITECTURE.md) – data flow and component design

## Grafana Dashboards

Dashboards are automatically provisioned at `http://127.0.0.1:3000` (unless `EXPOSE_UI=1`). Screenshots:

1. **Overview** – sync progress, block lag, CPU/RAM, chainstate size, reorg depth, and more.
2. **Sync Health** – headers vs blocks, block interval times, ZMQ liveness.
3. **Mempool & Fees** – backlog counts, fee histogram, fast/slow estimates.
4. **Peers & Geo** – world map, ASN breakdown, peer versions, churn.

## Grafana Alerting

Grafana 9+ unified alerting is included. Visit the Alerts UI to create rules such as “Block lag > 2 for 5 minutes” or “ZMQ rawblock stream idle for 2 minutes.” See [`docs/QUICKSTART.md`](docs/QUICKSTART.md#grafana-alerting-quickstart) for detailed guidance.

## Contributing

Contributions and issues are welcome! Please review [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and use the GitHub issue templates provided. Run `make test` (or see CI workflow) before submitting changes.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
