# Quick Start Guide

This quick start targets operators who already have a Bitcoin Core node running and want to
visualise metrics with the bundled stack without exploring every configuration option.
Follow the steps below and you should have dashboards in a few minutes.

## 1. Prerequisites

Follow the steps that match your operating system:

* **Linux (including WSL2 distributions):** install the Docker Engine and Docker Compose
  plugin from your distribution packages or directly from Docker. Ensure your user is part
  of the `docker` group or run the commands below with `sudo`.
* **Windows 10/11:** install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  with the WSL2 backend enabled. Run the commands below from an elevated PowerShell or
  Windows Terminal session. Docker Desktop ships with the Compose plugin already enabled.
* A synchronised Bitcoin Core node reachable from the collector container. Linux deployments
  expose the Docker host as `host.docker.internal`, which is the default RPC host for this
  stack. Ensure JSON-RPC is enabled and,
  if you plan to collect ZMQ metrics (`ENABLE_ZMQ=1`), configure the following publishers in
  `bitcoin.conf`:

  ```ini
  server=1
  rpcbind=127.0.0.1
  rpcallowip=127.0.0.1
  zmqpubrawblock=tcp://127.0.0.1:28332
  zmqpubrawtx=tcp://127.0.0.1:28333
  ```

* Optional: a Fulcrum/Electrs server exposing the `/stats` endpoint and a MaxMind account
  if you want GeoIP enrichment. When you intend to collect `bitcoind` process metrics, plan
  to run the collector with host PID visibility (for example by adding `pid: host` in a
  Docker Compose override file) or run it directly on the host so the process is visible to
  `psutil`.

## 2. Configure Environment

1. Copy the example environment file and edit it to match your node:

   * **Linux:**

     ```bash
     cp .env.example .env
     $EDITOR .env
     ```

   * **Windows PowerShell:**

     ```powershell
     Copy-Item .env.example .env
     notepad.exe .env
     ```

2. Set the following minimum values:

   | Variable | Description |
   |----------|-------------|
   | `BITCOIN_RPC_HOST` / `BITCOIN_RPC_PORT` | Location of your Bitcoin Core RPC endpoint. Defaults to `host.docker.internal` so the collector can reach a node running on the Docker host. |
   | `BITCOIN_RPC_USER` / `BITCOIN_RPC_PASSWORD` | RPC credentials, or leave blank to use the cookie file. |
   | `BITCOIN_DATADIR` | Absolute path mounted into the collector container for cookie access. Docker Compose does not expand `~`, so set this explicitly (for example `/home/bitcoin/.bitcoin`). Leave empty when the directory is not mounted. |
   | `BITCOIN_CHAINSTATE_DIR` | Path sampled for disk usage metrics. Defaults to a `chainstate` subdirectory under the data directory; clear the value when the mount is unavailable or you do not need the dashboard panels. |
   | `ENABLE_ZMQ` | Set to `1` only when you want ZMQ freshness metrics. Leave it at `0` otherwise. |
   | `BITCOIN_ZMQ_RAWBLOCK` / `BITCOIN_ZMQ_RAWTX` | When ZMQ metrics are enabled, ensure these match `bitcoin.conf`. Leave them commented to skip ZMQ panels. |
   | `INFLUX_SETUP_USERNAME` / `INFLUX_SETUP_PASSWORD` | Credentials used to bootstrap the bundled InfluxDB instance. |
   | `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` | Initial Grafana login. Replace the placeholder password in `.env` with a unique value before exposing dashboards. |
   | `FULCRUM_STATS_URL` | Leave blank unless you have a Fulcrum/Electrs instance exposing `/stats`. |

Most deployments can leave the defaults in place: the collector expects `chainstate` to live
under the data directory. Only point `BITCOIN_CHAINSTATE_DIR` somewhere else when you store
the database on a different volume, or clear the value when the path is not mounted and you
want to skip the disk usage panels.

3. Remember that the collector runs inside a container: use addresses that are reachable from
   that environment. When your node runs on the same machine as Docker, the bundled
   configuration already points to `host.docker.internal`. If the node lives elsewhere,
   adjust `BITCOIN_RPC_HOST`, `BITCOIN_ZMQ_*`, and mount the cookie file via a bind mount or
   provide explicit RPC credentials. You can omit the ZMQ entries entirely when the
   dashboards do not require those metrics.

## 3. Start the Stack

1. Launch InfluxDB, Grafana, the collector, and GeoIP update containers:

   * **Linux:**

     ```bash
     docker compose --profile bundled-influx --profile bundled-grafana up -d
     ```

   * **Windows PowerShell:**

     ```powershell
     docker compose --profile bundled-influx --profile bundled-grafana up -d
     ```

   The profiles ensure that the bundled InfluxDB and Grafana instances start alongside the
   collector. The compose file also mounts the InfluxDB token file and GeoIP databases into
   the collector container; keep those volumes in place unless you manage credentials via an
   alternative mechanism. If you plan to connect to external services you can omit the
   profiles and customise the environment instead.

2. Check service health:

   * **Linux:**

     ```bash
     docker compose ps
     docker compose logs collector | tail
     ```

   * **Windows PowerShell:**

     ```powershell
     docker compose ps
     docker compose logs collector | Select-Object -Last 20
     ```

   The collector emits a log line each time the fast and slow loops complete. Failures to
   reach Bitcoin Core or InfluxDB are now logged explicitly (watch for "Influx write failed"
   entries) so connectivity issues surface quickly.

## 4. Access Grafana

1. Navigate to `http://127.0.0.1:3000/` (or the host/IP you configured) and log in with the
   credentials from `.env`.
2. Grafana auto-loads the dashboards from `grafana/dashboards`. Look for the “Bitcoin Node
   Overview” dashboard to validate data is flowing. When you plan to import the dashboards
   into an existing Grafana instead of the bundled container, follow the
   [External Grafana](OPERATIONS.md#external-grafana) workflow to rewrite the data source UID
   before importing.

## 5. Validate Metrics

* Run the collector health check to confirm configuration loading:

  * **Linux:**

    ```bash
    docker compose exec collector python -m collector --healthcheck
    ```

  * **Windows PowerShell:**

    ```powershell
    docker compose exec collector python -m collector --healthcheck
    ```

* Inspect the InfluxDB bucket:

  * **Linux:**

    ```bash
    docker compose exec influxdb influx query 'from(bucket:"btc_metrics") |> range(start: -5m) |> limit(n:5)'
    ```

  * **Windows PowerShell:**

    ```powershell
    docker compose exec influxdb influx query "from(bucket:'btc_metrics') |> range(start: -5m) |> limit(n:5)"
    ```

If you see recent points and Grafana panels populate, you are ready to operate the stack.
Continue to the comprehensive guides for deeper configuration or production hardening.
