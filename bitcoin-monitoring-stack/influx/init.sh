#!/usr/bin/env bash
set -euo pipefail

if [ -z "${INFLUX_SETUP_USERNAME:-}" ] || [ -z "${INFLUX_SETUP_PASSWORD:-}" ]; then
  echo "INFLUX_SETUP_USERNAME and INFLUX_SETUP_PASSWORD must be provided" >&2
  exit 1
fi

ORG=${INFLUX_ORG:-bitcoin}
BUCKET=${INFLUX_BUCKET:-btc_metrics}
RETENTION_DAYS=${INFLUX_RETENTION_DAYS:-60}
TOKEN_FILE=/var/lib/influxdb2/.influxdbv2/token

if influx bucket list >/dev/null 2>&1; then
  echo "InfluxDB already initialized"
  exit 0
fi

SETUP_TOKEN=$(influx setup --skip-verify --bucket "${BUCKET}" --org "${ORG}" \
  --username "${INFLUX_SETUP_USERNAME}" --password "${INFLUX_SETUP_PASSWORD}" \
  --force --retention "$((RETENTION_DAYS*24))h" --token "${INFLUX_TOKEN:-}" | awk '/User/ {print $2}')

echo "Setup token: ${SETUP_TOKEN}"

if [ -z "${INFLUX_TOKEN:-}" ]; then
  echo -n "${SETUP_TOKEN}" > "${TOKEN_FILE}"
else
  echo -n "${INFLUX_TOKEN}" > "${TOKEN_FILE}"
fi

chmod 600 "${TOKEN_FILE}"
