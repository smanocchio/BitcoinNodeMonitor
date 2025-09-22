# Security Hardening

The default Docker Compose configuration binds all services to localhost for safety. If you
intend to expose dashboards or APIs beyond a trusted machine, apply the hardening
recommendations below.

## Network Exposure

* Keep `EXPOSE_UI=0` unless you need remote Grafana access. When enabling remote access,
  restrict exposure using a reverse proxy with TLS and authentication (for example, Nginx or
  Traefik) instead of publishing Docker ports directly.
* Place the monitoring stack on a dedicated network segment or VPN when it needs to reach a
  remote Bitcoin Core instance. Avoid exposing RPC ports publicly.
* Configure firewall rules so only the collector host can reach the Bitcoin Core RPC and ZMQ
  endpoints.

## Secrets Management

* Store `.env` with restrictive file permissions (`chmod 600 .env`).
* Prefer cookie-based authentication for Bitcoin Core when the collector runs on the same
  host. Cookies rotate automatically and never reside in version control.
* Rotate the InfluxDB API token regularly and avoid committing it to the repository. Use
  Docker secrets or environment-specific secret stores when running in production.

## Service Accounts

* Create dedicated OS users when running Docker on a multi-user system so that only trusted
  administrators can read data volumes.
* In hosted environments, deploy InfluxDB and Grafana with distinct credentials for the
  collector and the dashboard viewers. Grafana supports organisation and role-based access
  control to limit dashboard modifications.

## TLS and Encryption

* Terminate TLS at the reverse proxy in front of Grafana if exposing over the internet.
* For external InfluxDB deployments, prefer HTTPS endpoints (`INFLUX_URL=https://...`) and
  validate certificates. Use mutual TLS when offered by the service provider.
* Secure RPC traffic between the collector and Bitcoin Core with an SSH tunnel or VPN when
  traversing untrusted networks.

## System Updates

* Rebuild the collector container periodically (`docker compose build collector`) to pick up
  dependency patches such as `requests`, `psutil`, and `pyzmq`.
* Track upstream releases of InfluxDB, Grafana, and `geoipupdate` to inherit security fixes.
* Subscribe to Bitcoin Core release notes to ensure RPC/ZMQ interfaces remain compatible.

## Auditing and Logging

* Enable audit logging in Grafana for administrator actions if operating in a team
  environment.
* Export InfluxDB logs to your central logging solution to monitor authentication failures or
  unusual query patterns.
* Keep Docker daemon logs and system package updates in your existing compliance pipeline.

Applying these controls reduces the risk of credential leakage or remote exploitation while
still allowing the monitoring stack to provide actionable insights.
