# Troubleshooting Playbook

Use this playbook to diagnose common issues observed when running the Bitcoin Node
Monitoring Stack. Each section lists symptoms, likely causes, and concrete steps to
investigate.

## Collector Fails to Start

**Symptoms**

* Container exits immediately.
* Logs show `RuntimeError: pyzmq is required for ZMQListener` or missing dependency errors.

**Actions**

1. Rebuild the collector image to ensure dependencies are installed:
   `docker compose build collector`.
2. Verify that the Python runtime is ≥3.11 (set in `collector/pyproject.toml`).
3. Ensure the host provides network connectivity to the RPC and ZMQ endpoints.

## RPC Authentication Errors

**Symptoms**

* Collector logs display HTTP 401 or messages referencing `RPC error -32601`.
* Health check reports failure to load configuration.

**Actions**

1. Confirm `BITCOIN_RPC_USER`/`BITCOIN_RPC_PASSWORD` in `.env` match the node.
2. When using cookie auth, verify the cookie file path is mounted:
   `docker compose exec collector ls /root/.bitcoin/.cookie`.
3. Inspect `bitcoin.conf` for `rpcallowip` restrictions preventing the collector from
   connecting.

## Missing ZMQ Metrics

**Symptoms**

* Grafana panels showing ZMQ staleness display `NaN` or large `seconds_since` values.
* Collector logs warn about timeouts waiting for messages.

**Actions**

1. Confirm the ZMQ endpoints in `.env` match `bitcoin.conf`.
2. Ensure the host firewall allows the collector to connect to the ZMQ ports.
3. Restart Bitcoin Core to re-establish ZMQ publishers if necessary.

## InfluxDB Write Failures

**Symptoms**

* Collector logs contain `requests.exceptions.HTTPError` or `Failed to write points`.
* Grafana dashboards stop updating.

**Actions**

1. Check InfluxDB health: `docker compose exec influxdb influx ping`.
2. Ensure the bucket and organisation names match the environment variables.
3. If pointing at an external InfluxDB, verify the API token has the `write` permission for
   the bucket.
4. Inspect available disk space on the InfluxDB host.

## Grafana Cannot Authenticate

**Symptoms**

* Login screen rejects credentials defined in `.env`.

**Actions**

1. If you changed the password inside Grafana, update `.env` so container restarts retain the
   new value.
2. Delete the `grafana-data` volume to reset credentials (warning: removes saved dashboards).
3. Check the container logs for messages about LDAP or OAuth if custom auth was configured.

## GeoIP Data Missing

**Symptoms**

* Peer dashboards show “Unknown” for country or ASN fields.

**Actions**

1. Ensure `geoipupdate` container is running: `docker compose ps geoipupdate`.
2. Review `docker compose logs geoipupdate` for authentication errors. Invalid MaxMind
   credentials will be reported here.
3. Confirm the collector sees the databases:
   `docker compose exec collector ls /usr/share/GeoIP/GeoLite2-*.mmdb`.
4. When credentials are corrected, restart both `geoipupdate` and `collector` containers.

## General Diagnostics

* Use `docker compose logs <service>` with the `--since` flag to filter recent events.
* Run ad-hoc RPC commands from the collector container:

  ```bash
  docker compose exec collector python - <<'PY'
  from collector.bitcoin_rpc import BitcoinRPC
  from collector.config import load_config

  cfg = load_config()
  rpc = BitcoinRPC(
      f"http://{cfg.bitcoin_rpc_host}:{cfg.bitcoin_rpc_port}",
      username=cfg.bitcoin_rpc_user,
      password=cfg.bitcoin_rpc_password,
      cookie=cfg.cookie_path and (cfg.cookie_path.read_text().split(':', 1))
  )
  print(rpc.get_blockchain_info())
  PY
  ```

* Query InfluxDB directly to verify data presence:

  ```bash
  docker compose exec influxdb influx query 'from(bucket:"btc_metrics") |> range(start: -1h) |> count()'
  ```

By following these targeted steps you can resolve most issues without needing to rebuild the
entire environment.
