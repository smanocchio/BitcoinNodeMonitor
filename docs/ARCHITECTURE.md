# Architecture and Data Flow

The monitoring stack is intentionally modular so that each concern can be operated
independently or swapped out for an external equivalent. This document dives into the major
components, the data exchanged between them, and the internal structure of the collector.

## High-Level Topology

```
┌────────────┐       JSON-RPC/ZMQ       ┌─────────────────┐      Line Protocol      ┌─────────────┐
│ Bitcoin    │ ───────────────────────▶ │ Collector        │ ──────────────────────▶ │ InfluxDB    │
│ Core Node  │                         │ (Python)         │                          │ (TimeSeries)│
└────────────┘   Fulcrum / GeoIP       └─────────────────┘        Flux Queries       └─────┬───────┘
       ▲                ▲                                             │                  │
       │                │                                             ▼                  ▼
       │                │                                        Grafana Dashboards   External
       │                └── GeoLite2 databases via `geoipupdate`                         clients
```

* **Bitcoin Core** supplies blockchain state, mempool details, peer metadata, and block/tx
  announcements via JSON-RPC and ZMQ.
* **Collector** orchestrates metric scraping, enrichment, and fan-out to InfluxDB.
* **InfluxDB** persists the time-series data in the configured bucket and retention policy.
* **Grafana** issues Flux queries to InfluxDB and renders dashboards.
* **GeoIP Update** container keeps the MaxMind GeoLite databases fresh for ASN and country
  lookups.

Each box can be replaced with an external service: point the collector at a remote
InfluxDB/Grafana pair, or disable GeoIP updates when enrichment is not required.

## Collector Internals

The collector is a Python application located under `collector/collector`. It combines
synchronous RPC calls with asynchronous scheduling:

* **Configuration** – `CollectorConfig` is built from environment variables via
  `pydantic-settings`. Defaults mirror the `.env.example` file and may be overridden per
  deployment.
* **Startup** – `CollectorService` initialises helper objects: `BitcoinRPC`, `InfluxWriter`,
  `GeoIPResolver`, `FulcrumClient`, `ReorgTracker`, and a threaded `ZMQListener` subscribed
  to raw block/transaction streams.
* **Concurrency model** – two asynchronous loops (`_fast_loop` and `_slow_loop`) run in
  parallel. Each loop schedules blocking work onto threads so that RPC calls do not block the
  event loop. Intervals are governed by `SCRAPE_INTERVAL_FAST` and `SCRAPE_INTERVAL_SLOW`.
* **Retry strategy** – the fast and slow collectors are wrapped in `tenacity.retry` with
  exponential backoff. Transient RPC or network failures are retried up to three attempts
  before surfacing as log entries.

### Fast Loop Responsibilities

Runs every few seconds to capture rapidly changing metrics:

* Blockchain height, headers height, verification progress, and difficulty (`getblockchaininfo`).
* Reorganisation depth estimated by `ReorgTracker`, using recent height history.
* ZMQ listener liveness (seconds since last message and counts per topic).
* Mempool size, weight, and fee estimates (via `getmempoolinfo` and `estimatesmartfee`).
* Optional mempool histogram aggregation using either `getrawmempool` buckets or the
  external mempool.space API.

### Slow Loop Responsibilities

Runs less frequently to capture heavier queries:

* Peer counts (total, inbound, outbound) and ping latency percentiles derived from
  `getpeerinfo`.
* Optional process metrics from `psutil`, targeting the `bitcoind` process by name. The
  collector requires host PID visibility (for example `pid: host`) or a host deployment to
  observe the process from inside a container.
* Optional disk usage sampling for the chainstate directory.
* Optional Fulcrum/Electrs statistics pulled from the configured stats endpoint.

### Data Serialization

Metrics are transformed into `Point` objects (measurement, tags, fields) defined in
`collector/influx.py`. Points are translated to InfluxDB line protocol and transmitted via
HTTP to `/api/v2/write`. All measurements are tagged with the Bitcoin network to simplify
multi-network deployments.

## Supporting Services

### InfluxDB Bootstrap

The `influx/init.sh` script initialises a fresh InfluxDB instance by calling `influx setup`.
It creates the configured organisation, bucket, retention policy, and API token, persisting
credentials to `/var/lib/influxdb2/.influxdbv2/token` for the collector to read.

### Grafana Provisioning

Grafana is pre-loaded with:

* **Data source** – defined in `grafana/provisioning/datasources/datasource.yml`. It points
  to the InfluxDB service using Flux queries and injects credentials from environment
  variables.
* **Dashboards** – JSON exports stored in `grafana/dashboards/*.json`. Provisioning is
  handled via `grafana/provisioning/dashboards`. The dashboards cover overall status, sync
  health, mempool fees, and peer geography (leveraging GeoIP enrichment).

### GeoIP Update

The `geoipupdate` container periodically downloads MaxMind GeoLite2 city and ASN databases
into a shared volume mounted by the collector. `GeoIPResolver` opens these files on startup
and exposes country/ASN lookups for peer IP addresses. When the databases are missing the
collector gracefully returns `None` for those fields.

## Extending the Stack

* **Additional Metrics** – add new helper functions in `collector/collector/metrics.py` and
  emit extra `Point` objects from the fast or slow loops.
* **External Dashboards** – connect Grafana to additional data sources or write custom Flux
  queries against the InfluxDB bucket.
* **Alternate Storage** – the collector only depends on the InfluxDB HTTP API. Point it at a
  managed InfluxDB Cloud instance by overriding `INFLUX_URL`, `INFLUX_TOKEN`, and the
  organisation/bucket settings.

By keeping boundaries clean the project can be deployed all-in-one for home labs or
integrated piecemeal into existing observability pipelines.
