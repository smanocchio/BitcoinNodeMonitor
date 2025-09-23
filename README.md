# Bitcoin Node Monitoring Stack

The Bitcoin Node Monitoring Stack ships a self-contained toolkit for watching the
health, performance, and network activity of a Bitcoin Core node. The project combines a
lightweight metrics collector with an InfluxDB time-series database, curated Grafana
dashboards, and optional GeoIP enrichment so that operators can understand node behaviour at
a glance.

The stack is designed for operators who want to:

* Observe blockchain synchronisation, mempool volume, and peer connectivity in real time.
* Track operating-system level resource usage and disk growth for the node data directory.
* Record metrics in InfluxDB for long-term retention and historical analysis.
* Visualise the results through Grafana dashboards that are provisioned automatically.

The repository contains the Docker assets needed to run the full stack as well as the
Python collector service that queries Bitcoin Core over RPC, monitors ZMQ block/transaction
streams, and pushes metrics to InfluxDB.

> **Heads up:** Docker Compose does **not** expand `~` inside volume mappings. Set
> `BITCOIN_DATADIR` in your `.env` file to the absolute path of the Bitcoin Core data
> directory you want to mount into the collector container. Without the bind mount the
> collector cannot read the RPC cookie or sample disk utilisation.

## Components at a Glance

| Component | Purpose | Implementation Details |
|-----------|---------|------------------------|
| Collector | Scrapes Bitcoin Core, Fulcrum, ZMQ, and host metrics before pushing points to InfluxDB. | `collector/collector` Python package (async event loops, retry logic, GeoIP lookup). |
| InfluxDB  | Stores metrics produced by the collector. Can be bundled via Docker or pointed at an existing cluster. | Official `influxdb:2.7` image with bootstrap script under `influx/init.sh`. |
| Grafana   | Renders curated dashboards and connects to InfluxDB using Flux queries. | Provisioned by files in `grafana/provisioning` and dashboards under `grafana/dashboards`. |
| GeoIP     | Periodically downloads MaxMind GeoLite2 databases for peer geography insights. | Managed via the `geoipupdate` container and configuration template in `geoip/`. |
| Dashboards | Ready-to-use Grafana dashboards grouped by topic (overview, sync, mempool, peers). | JSON exports located in `grafana/dashboards`. |

## Data Flow Summary

1. **Bitcoin Core** exposes JSON-RPC, ZMQ block/transaction streams, and optionally Fulcrum
   statistics.
2. **Collector** authenticates using RPC credentials or the cookie file, polls data at
   configurable fast/slow intervals (fast for blockchain and mempool changes, slow for
   peer/process/disk sampling), enriches with GeoIP lookups, and writes metrics to
   InfluxDB.
3. **InfluxDB** stores the time-series data inside the configured bucket and retention
   policy.
4. **Grafana** connects to InfluxDB using a provisioned data source and renders the bundled
   dashboards.

## Repository Layout

```
collector/            Python package and Docker image for the collector
  ├── collector/      Core source modules
  └── tests/          Unit tests for configuration and metrics helpers
geoip/                GeoIP update configuration template
influx/               Bootstrap script for setting up the bundled InfluxDB instance
grafana/              Provisioning configs and exported dashboards
docs/                 Comprehensive guides (architecture, configuration, operations)
docker-compose.yml    Orchestrates the optional InfluxDB, Grafana, collector, and GeoIP containers
.env.example          Template environment file covering the collector and services
```

## Documentation Map

* [`docs/QUICKSTART.md`](docs/QUICKSTART.md) – minimal setup aimed at operators who just
  need the essentials.
* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) – in-depth look at each component and
  their interactions.
* [`docs/CONFIG.md`](docs/CONFIG.md) – full reference of configuration knobs, environment
  variables, and feature flags.
* [`docs/OPERATIONS.md`](docs/OPERATIONS.md) – day-two tasks: running, upgrading, backups,
  and verifying data flow.
* [`docs/HARDENING.md`](docs/HARDENING.md) – security considerations when exposing services
  beyond localhost.
* [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) – symptom-based debugging playbooks.
* [`docs/PORTAINER.md`](docs/PORTAINER.md) – how to deploy the stack as a Portainer-managed
  stack using the bundled Compose file.

### Operating System Notes

The stack runs anywhere Docker is available. The quick start guide now contains parallel
instructions for Linux hosts (including WSL2) and Windows hosts using PowerShell alongside
Docker Desktop, so you can follow the workflow that matches your environment.

Change the default Grafana administrator password in `.env` before exposing the dashboards
to anyone else. The sample configuration now uses a placeholder value to remind you to set a
unique secret for your deployment.

## Contributing

Pull requests are welcome for new metrics, dashboard enhancements, or operational guides.
Run the collector unit tests with `pytest` inside the `collector/` directory before
submitting changes. For significant work please open an issue describing the motivation and
proposed approach.
