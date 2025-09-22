# Quick Start Guide

This quick start targets operators who already have a Bitcoin Core node running and want to
visualise metrics with the bundled stack without exploring every configuration option.
Follow the steps below and you should have dashboards in a few minutes.

## 1. Prerequisites

* Docker Engine and Docker Compose Plugin installed on the host that will run the
  monitoring containers.
* A synchronised Bitcoin Core node reachable from the host. Enable JSON-RPC and ZMQ with
  the following options in `bitcoin.conf` if they are not already set:

  ```ini
  server=1
  rpcbind=127.0.0.1
  rpcallowip=127.0.0.1
  zmqpubrawblock=tcp://127.0.0.1:28332
  zmqpubrawtx=tcp://127.0.0.1:28333
  ```

* Optional: a Fulcrum/Electrs server exposing the `/stats` endpoint and a MaxMind account
  if you want GeoIP enrichment.

## 2. Configure Environment

1. Copy the example environment file and edit it to match your node:

   ```bash
   cp .env.example .env
   $EDITOR .env
   ```

2. Set the following minimum values:

   | Variable | Description |
   |----------|-------------|
   | `BITCOIN_RPC_HOST` / `BITCOIN_RPC_PORT` | Location of your Bitcoin Core RPC endpoint. |
   | `BITCOIN_RPC_USER` / `BITCOIN_RPC_PASSWORD` | RPC credentials, or leave blank to use the cookie file. |
   | `BITCOIN_DATADIR` | Path mounted into the collector container for cookie access. |
   | `BITCOIN_ZMQ_RAWBLOCK` / `BITCOIN_ZMQ_RAWTX` | Must match the ZMQ configuration from `bitcoin.conf`. |
   | `INFLUX_SETUP_USERNAME` / `INFLUX_SETUP_PASSWORD` | Credentials used to bootstrap the bundled InfluxDB instance. |
   | `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` | Initial Grafana login. |

3. If the monitoring host is different from the Bitcoin node, adjust `BITCOIN_RPC_HOST`,
   `BITCOIN_ZMQ_*`, and mount the cookie file via a bind mount or provide explicit RPC
   credentials.

## 3. Start the Stack

1. Launch InfluxDB, Grafana, the collector, and GeoIP update containers:

   ```bash
   docker compose --profile bundled-influx --profile bundled-grafana up -d
   ```

   The profiles ensure that the bundled InfluxDB and Grafana instances start alongside the
   collector. If you plan to connect to external services you can omit the profiles and
   customise the environment instead.

2. Check service health:

   ```bash
   docker compose ps
   docker compose logs collector | tail
   ```

   The collector emits a log line each time the fast and slow loops complete. Failures to
   reach Bitcoin Core or InfluxDB will be logged here.

## 4. Access Grafana

1. Navigate to `http://127.0.0.1:3000/` (or the host/IP you configured) and log in with the
   credentials from `.env`.
2. Grafana auto-loads the dashboards from `grafana/dashboards`. Look for the “Bitcoin Node
   Overview” dashboard to validate data is flowing.

## 5. Validate Metrics

* Run the collector health check to confirm configuration loading:

  ```bash
  docker compose exec collector python -m collector --healthcheck
  ```

* Inspect the InfluxDB bucket:

  ```bash
  docker compose exec influxdb influx query 'from(bucket:"btc_metrics") |> range(start: -5m) |> limit(n:5)'
  ```

If you see recent points and Grafana panels populate, you are ready to operate the stack.
Continue to the comprehensive guides for deeper configuration or production hardening.
