# Hardening Guide

The monitoring stack ships with conservative defaults (loopback-only bindings, read-only mounts). Follow these steps before exposing services beyond localhost.

## 1. Restrict Access

- Keep `EXPOSE_UI=0` unless you have a firewall protecting port `3000` (Grafana) and `8086` (InfluxDB).
- If you must expose to your LAN, set in `.env`:
  ```
  EXPOSE_UI=1
  GRAFANA_BIND_IP=0.0.0.0
  INFLUX_BIND_IP=0.0.0.0
  ```
  Then ensure your LAN firewall blocks internet access and apply the protections below.

## 2. Create a Read-Only RPC User

Edit `bitcoin.conf`:

```
rpcuser=monitor
rpcpassword=<strong-unique-password>
rpcwhitelist=monitor@127.0.0.1
rpcauth=<generated using bitcoin-cli rpcuser ...>
```

Restart Bitcoin Core and update `.env` with the new credentials. Avoid sharing your full-access wallet RPC credentials.

## 3. Rotate InfluxDB and Grafana Passwords

- After first login, change the Grafana admin password under **Administration → Users**.
- Run `docker compose exec influxdb influx auth list` to retrieve tokens. Regenerate or scope tokens to write-only for the collector.

## 4. Enable HTTPS via Reverse Proxy

Place Grafana and InfluxDB behind a TLS-terminating proxy. Examples below bind to `127.0.0.1` and re-publish securely.

### Caddy Example

```
monitor.example.com {
  reverse_proxy 127.0.0.1:3000
  header Content-Security-Policy "frame-ancestors 'self'"
}
```

### Traefik (docker-compose snippet)

```
  traefik:
    image: traefik:v2.10
    command:
      - "--entrypoints.web.address=:80"
      - "--providers.docker=true"
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  grafana:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`monitor.example.com`)"
      - "traefik.http.routers.grafana.entrypoints=web"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"
```

Add TLS (`--entrypoints.websecure.address=:443`, certificates, etc.) as desired.

## 5. Lock Down Grafana

- Disable user sign-up (`GF_USERS_ALLOW_SIGN_UP=false`, already set).
- Configure auth proxies/OAuth if integrating with an identity provider.
- Limit alert contact points to trusted channels.

## 6. Secure GeoIP Data

- GeoLite2 licenses restrict sharing. Store the downloaded databases on encrypted storage if they contain sensitive logs.
- Set `GEOIP_UPDATE_FREQUENCY_DAYS` to a reasonable value (weekly) to reduce attack surface.

## 7. System Hardening

- Run Docker as a non-root user where possible.
- Keep host OS patched and Bitcoin Core updated.
- Monitor Docker logs for unexpected access attempts.

## 8. Backups & Disaster Recovery

- Back up the `influx-data` and `grafana-data` volumes if dashboards or retention policies are critical.
- Export Grafana dashboards periodically (`Dashboards → JSON model → Save to file`).

By following these practices you can safely expose the monitoring stack to a trusted network while minimizing risk.
