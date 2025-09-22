# Architecture Overview

```
┌─────────────┐    RPC / ZMQ     ┌────────────────┐   Line protocol   ┌─────────────┐   Queries   ┌─────────────┐
│ Bitcoin Core├─────────────────▶│ Python Collector├─────────────────▶│  InfluxDB 2  │────────────▶│   Grafana    │
└─────────────┘                  └────────────────┘                   └─────────────┘             └─────────────┘
       ▲                                 │  GeoIP/ASN lookup (optional)          ▲                        │
       │                                 └──────────────┬────────────────────────┘                        │
       │                                                │                                                 │
       │                                         ┌──────────────┐                                          │
       │                                         │ Fulcrum /    │                                          │
       │                                         │ Electrs API  │                                          │
       │                                         └──────────────┘                                          │
       │                                                                                                Alerts
       └───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Components

- **Bitcoin Core** – Provides blockchain, mempool, and network data through RPC and ZMQ streams.
- **Python Collector** – Modular scraper that polls RPC endpoints, listens to ZMQ notifications, enriches peer data with GeoIP/ASN metadata, and forwards metrics to InfluxDB.
- **InfluxDB 2** – Stores time-series metrics. Bootstrapped with organization, bucket, retention policy, and API token. Exposes the Flux query API.
- **Grafana** – Visualizes metrics via dashboards and triggers alerts using Grafana's unified alerting.
- **GeoIP Updater** – (Optional) Downloads MaxMind GeoLite2 databases for country and ASN lookups.

## Data Flow

1. The collector reads configuration from environment variables using a Pydantic model. Optional autodetection locates the local cookie file and datadir.
2. Fast loop (5s default) polls block heights, mempool stats, ZMQ heartbeat, and process metrics. Slow loop (30s) fetches peer lists, disk usage, and optional Electrs/Fulcrum stats.
3. Metrics are batched into InfluxDB line protocol and written via the HTTP API. Tenacity retries handle transient failures.
4. Grafana connects to InfluxDB using a provisioned datasource and loads dashboards through provisioning files. Dashboards include template variables for network, node name, and feature flags.
5. Grafana alerting evaluates Flux queries and notifies configured contact points (email, Slack, Telegram, etc.).

## Resilience & Health

- Docker healthchecks ensure collector, InfluxDB, Grafana, and GeoIP services are responding.
- Collector gracefully degrades when optional components (GeoIP, Fulcrum, mempool histogram) are disabled.
- Pydantic validation stops startup when required configuration is missing.

## Extensibility

- Additional metrics modules can be added under `collector/metrics.py` and registered with the aggregator.
- Dashboards are JSON files compatible with Grafana provisioning; add new dashboards under `grafana/dashboards` and reference them in `dashboards.yml`.
- CI ensures Python linting, typing, tests, and docker compose validation pass before merging changes.
