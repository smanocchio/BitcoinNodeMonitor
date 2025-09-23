# Operations Guide

This guide covers the lifecycle of running the monitoring stack after the initial
installation: starting and stopping services, verifying data flow, performing maintenance,
and upgrading components.

## Running the Stack

### Start

```bash
docker compose --profile bundled-influx --profile bundled-grafana up -d
```

* Profiles allow you to include the bundled InfluxDB and Grafana services only when needed.
  Set `COMPOSE_PROFILES=bundled-influx,bundled-grafana` (or pass `--profile` flags as shown)
  to launch the local services, or omit the profiles entirely when pointing at external
  infrastructure.

> **Permissions:** The collector container now runs as an unprivileged `collector` user.
> Ensure the mounted Bitcoin datadir and Influx token file are readable by non-root users on
> the host (for example via `chmod 640` and group membership) so metrics scraping continues to
> work after the upgrade.

### Stop

```bash
docker compose down
```

* Add `--volumes` to remove persisted data (InfluxDB bucket, Grafana database, GeoIP files).
* For upgrades, prefer `docker compose pull` followed by `docker compose up -d` to download
  newer images while keeping volumes intact.

### Health Checks

* Collector: `docker compose exec collector python -m collector --healthcheck`
* InfluxDB: `docker compose exec influxdb influx ping`
* Grafana: `curl http://127.0.0.1:3000/api/health`

All containers define Docker health checks, which you can inspect via `docker compose ps`.

## Observability of the Collector

* Logs are emitted to stdout. Follow them with `docker compose logs -f collector`.
* Enable debug logs temporarily by setting `COLLECTOR_LOG_LEVEL=DEBUG` before starting the
  container.
* Metrics are submitted in batches; explicit "Influx write failed" log entries indicate the
  collector could not persist points. These errors trigger retries automatically, making it
  easier to alert on persistent write failures.
* When the chainstate directory is not mounted into the collector container the service logs
  "Skipping filesystem metrics" and continues publishing the remaining measurements instead
  of failing the slow loop.

## Managing Credentials

* Rotate InfluxDB tokens by editing `.env` and re-running `docker compose up -d`. The
  bootstrap script respects an explicit `INFLUX_TOKEN` value.
* Change Grafana administrator credentials either through `.env` or inside the Grafana UI.
  When using the UI remember to update the environment file so future container recreations
  do not revert the password.
* RPC credentials can be stored securely via the cookie mechanism; avoid embedding plaintext
  passwords when the collector runs on the same host as Bitcoin Core.

## GeoIP Database Maintenance

* Ensure `GEOIP_ACCOUNT_ID` and `GEOIP_LICENSE_KEY` are set. Without them the update job will
  fail and GeoIP enrichment will be absent from dashboards.
* To refresh immediately, run `docker compose run --rm geoipupdate geoipupdate`.
* When MaxMind publishes new database formats, update the `geoipupdate` image tag in
  `docker-compose.yml` accordingly.

## Using External Services

### External InfluxDB

1. Omit the `bundled-influx` profile (for example `COMPOSE_PROFILES=bundled-grafana` or by
   passing only `--profile bundled-grafana` on the command line).
2. Provide `INFLUX_URL`, `INFLUX_TOKEN`, `INFLUX_ORG`, and `INFLUX_BUCKET` for the remote
   instance.
3. Update Grafana provisioning to point at the external InfluxDB endpoint (environment
   variables propagate automatically).

### External Grafana

1. Omit the `bundled-grafana` profile when starting Docker Compose.
2. Import the JSON dashboards from `grafana/dashboards` into your existing Grafana.
3. Recreate the InfluxDB data source manually using the same organisation, bucket, and token
   configured for the collector.

## Upgrading the Collector

1. Pull the latest repository changes.
2. Rebuild the collector image: `docker compose build collector`.
3. Restart the service: `docker compose up -d collector`.
4. Review `docker compose logs collector` for startup messages and ensure metrics resume.

The collector adheres to semantic versioning. Breaking changes will be documented in the
project changelog (`CHANGELOG.md`).

## Backup and Restore

* **InfluxDB** – back up `/var/lib/influxdb2` (stored in the `influx-data` Docker volume).
  Use `docker run --rm -v influx-data:/data alpine tar czf - /data > influx-backup.tgz` to
  capture a snapshot.
* **Grafana** – dashboards live in the `grafana-data` volume; back up similarly if you create
  customisations.
* **Configuration** – keep a copy of `.env` and any overrides for docker-compose.

## Monitoring Bitcoin Core Health

Even though the stack focuses on metrics collection, it relies on a healthy Bitcoin Core
node. Keep an eye on:

* `bitcoind` logs for RPC or ZMQ errors.
* Adequate disk space on the host so that the chainstate directory can grow.
* Network reachability from the collector host to RPC/ZMQ endpoints.

Following these operational practices will keep dashboards accurate and reduce downtime when
components are restarted or upgraded.
