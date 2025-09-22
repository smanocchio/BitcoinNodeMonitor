# Troubleshooting

## Collector cannot connect to Bitcoin RPC

- **Symptom**: `401 Unauthorized` or `connection refused` in collector logs.
- **Fix**: Verify `BITCOIN_RPC_HOST`, `PORT`, and credentials. If using cookie auth, ensure the `.cookie` file is mounted read-only into the collector container (check volume mapping). On Windows paths, escape backslashes or use WSL paths (`/mnt/c/...`).

## RPC password contains special characters

- Wrap the value in single quotes when editing `.env` or escape special characters according to shell rules. Alternatively, create a dedicated read-only RPC user (see [`HARDENING.md`](HARDENING.md)).

## ZMQ metrics show `disconnected`

- Confirm that `bitcoin.conf` includes lines such as `zmqpubrawblock=tcp://127.0.0.1:28332` and `zmqpubrawtx=tcp://127.0.0.1:28333`.
- Ensure firewalls permit the ZMQ ports and that the endpoints in `.env` match your configuration.

## Grafana shows “Datasource not found”

- InfluxDB may not have finished bootstrapping. Run `docker compose logs influxdb` and wait for the `Initialization complete` message.
- If `INFLUX_TOKEN` is blank and bootstrap was interrupted, remove the `influx-data` volume (`docker volume rm bitcoin-monitoring-stack_influx-data`) and restart.

## Windows path quirks

- When using Docker Desktop with WSL, ensure the Bitcoin data directory is shared with Docker Desktop.
- Use `/mnt/c/...` paths in `.env`. If Grafana dashboards fail to load due to file permissions, run `wsl --shutdown` and restart Docker Desktop.

## GeoIP updates fail

- Check that `GEOIP_ACCOUNT_ID` and `GEOIP_LICENSE_KEY` are set. Free MaxMind accounts require EULA acceptance before downloads.
- If you don't need GeoIP, leave credentials blank and the collector will skip enrichment.

## Grafana alert not firing

- Unified alerting requires evaluation every minute. Ensure the rule's evaluation interval is shorter than the duration condition.
- Verify the query returns data by pressing **Preview** within the rule editor.
- Confirm a contact point is attached. Without one, alerts remain in the “No contact point” state.

## Collector healthcheck failing

- Run `docker compose logs collector` to inspect errors.
- Validate that InfluxDB token is present and Grafana/Influx hostnames resolve (DNS issues on custom networks can cause timeouts).
- If using feature flags, disable modules one-by-one (set to `0`) to isolate the failing component.

## Dashboard panels empty

- Ensure the collector has been running for at least a few minutes.
- If using testnet/signet, adjust the dashboard variable `Network` to match.

## Resetting the stack

```bash
docker compose down -v
rm -rf grafana/data influx/data
docker compose up -d
```

This removes persisted data (dashboards and metrics). Use only when you need a clean slate.
