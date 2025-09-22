# InfluxDB Bootstrap

`init.sh` runs on container startup to initialize InfluxDB 2.x using the credentials in `.env`.

It performs:

1. `influx setup` with the provided org, bucket, retention, username, and password.
2. Writes the resulting API token to `/var/lib/influxdb2/.influxdbv2/token` so the collector can read it.
3. Honours `INFLUX_TOKEN` if you prefer to manage tokens manually.

If you need to re-run the bootstrap, delete the `influx-data` volume:

```bash
docker compose down
docker volume rm bitcoin-monitoring-stack_influx-data
docker compose up -d
```
