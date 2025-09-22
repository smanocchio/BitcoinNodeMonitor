# Deploying with Portainer

Portainer can manage the Docker Compose stack that powers Bitcoin Node Monitoring. This guide walks through uploading the repository's Compose file as a Portainer stack and mapping the persistent volumes required by InfluxDB, Grafana, and the GeoIP updater.

## Prerequisites

* A Portainer instance with access to the Docker environment that will run the monitoring containers.
* The ability to reach your Bitcoin Core node from the Portainer-managed host. RPC and ZMQ endpoints must be accessible from the Docker network just like the standard Compose workflow.
* The repository cloned locally, or a copy of the [`docker-compose.yml`](../docker-compose.yml) file that ships with the project.

## 1. Prepare Environment Variables

Portainer lets you provide an `.env` file when you create a stack. Use the same values that are required in the [Quick Start guide](./QUICKSTART.md):

1. Copy `.env.example` to `.env` and adjust RPC credentials, the data directory mount, ZMQ endpoints, and Grafana/InfluxDB bootstrap credentials.
2. Ensure any host paths referenced in the `.env` file are valid on the Docker host that Portainer manages. These paths are mounted into the containers just like when running `docker compose` locally.

If you cannot supply an `.env` file (for example when pasting Compose content into the web editor) you can replace the `${VARIABLE}` expressions in the compose file with their literal values. Be mindful not to commit secrets back into version control if you download an edited file.

## 2. Create a Portainer Stack

1. Log in to Portainer and choose the environment where you want to deploy the monitoring stack.
2. Navigate to **Stacks → Add stack**.
3. Give the stack a name such as `bitcoin-node-monitor`.
4. Upload the repository's `docker-compose.yml` file or paste its contents into the web editor.
5. Attach your `.env` file under **Environment variables** if you prepared one earlier.
6. Enable the **bundled-influx** and **bundled-grafana** profiles if you want Portainer to start the local InfluxDB and Grafana containers. In the Portainer UI you can do this by adding the following to the **Environment variables** section:

   ```
   COMPOSE_PROFILES=bundled-influx,bundled-grafana
   ```

   Alternatively, you can edit the compose file before uploading it to include the services you want Portainer to manage.
7. Deploy the stack.

Portainer will create the same services defined in `docker-compose.yml`. You can watch container logs from the stack view to confirm that the collector connects to Bitcoin Core and InfluxDB.

## 3. Validate the Deployment

After the stack finishes deploying, follow the same validation steps described in the [Quick Start guide](./QUICKSTART.md#5-validate-metrics):

* Use the **Containers** view in Portainer to open a console into the collector container and run `python -m collector --healthcheck`.
* Use the InfluxDB console or Portainer's log viewer to confirm that measurements are being written to the `btc_metrics` bucket.
* Visit Grafana at the host/port you exposed (typically `http://<docker-host>:3000/`) and sign in with the credentials from `.env`.

## 4. Persisting Data Volumes

The compose file defines named volumes for InfluxDB, Grafana, and the GeoIP database cache. Portainer will create these volumes automatically. You can review them under **Volumes** in the Portainer navigation and configure backups or snapshots as desired.

If you prefer to bind-mount host directories instead of using named volumes, edit the compose file before uploading it to Portainer and replace the volume definitions with the host paths you want to use.

## 5. Updating the Stack

To upgrade the monitoring stack when new releases land:

1. Download the latest `docker-compose.yml`, `.env.example`, and any other relevant files from the repository.
2. In Portainer, open your stack and choose **Editor → Upload** to replace the compose file with the updated version.
3. Apply the update. Portainer will recreate the services while preserving named volumes so data in InfluxDB and Grafana remains intact.

Refer to [docs/OPERATIONS.md](./OPERATIONS.md) for additional day-two operational guidance once the stack is running.
