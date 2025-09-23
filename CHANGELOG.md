# Changelog

All notable changes to this project will be documented here.

## [Unreleased]
- Mount InfluxDB token and GeoIP databases into the collector to enable automatic
  authentication and GeoIP enrichment out of the box.
- Stop printing the InfluxDB API token during bootstrap and document the change.
- Enrich peer metrics with GeoIP country/ASN aggregates when databases are present.
- Treat an empty Fulcrum stats URL as disabled and update docs to highlight optional
  dependencies and host PID requirements for process metrics.
- Add CI guardrails running Ruff, MyPy, pytest, docker compose config validation, and secret
  scanning.

## [0.1.0] - 2023-11-01
- Initial release of the Bitcoin Monitoring Stack
- Python collector, Docker Compose deployment, Grafana dashboards, and documentation
