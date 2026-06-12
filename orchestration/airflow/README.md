# EntityQ Airflow Orchestration

This folder contains the Airflow layer for the EntityQ quality workflow.

## What the DAG does

The DAG orchestrates the local EntityQ workflow in this order:

1. `run_core_pipeline`
2. `run_new_dataset_onboarding`
3. `run_sql_quality_checks`
4. `run_remediation_workflow`

Kafka is intentionally excluded from the default DAG because it requires a running local Kafka broker.

## How to start Airflow with Docker Compose

From this folder:

```bash
cd orchestration/airflow
docker compose up airflow-init
docker compose up -d
docker compose ps
```

## How to open the Airflow UI

Open `http://localhost:8080` in your browser after the services are up.

If port 8080 is already in use, start the stack with another host port:

```bash
AIRFLOW_WEBSERVER_PORT=8081 docker compose up -d
```

The default local demo credentials are:

- Username: `airflow`
- Password: `airflow`

## How to trigger the DAG

In the Airflow UI, open the `entityq_quality_pipeline` DAG and trigger it manually.

## How to stop the environment

```bash
docker compose down --volumes --remove-orphans
```

## Implementation notes

The Docker Compose stack mounts the project root at `/opt/airflow/entityq` and sets `PYTHONPATH=/opt/airflow/entityq/src` so the DAG can run the local EntityQ modules directly.
