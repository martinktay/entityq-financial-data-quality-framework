# EntityQ Airflow Orchestration

## Purpose

This document explains how the EntityQ data quality workflow is orchestrated with Apache Airflow in local Docker Compose.

Airflow is intentionally isolated under `orchestration/airflow/` so the core Python package can still run without a local Airflow installation.

## Local Airflow Stack

The Compose stack runs:

- `airflow-db`: Postgres metadata database
- `airflow-init`: database migration and local admin user creation
- `airflow-webserver`: Airflow UI on `http://localhost:8080`
- `airflow-scheduler`: DAG scheduler

The Docker image starts from `apache/airflow:2.9.3-python3.11`, installs only the EntityQ dependencies needed by the DAG runtime, mounts the repository at `/opt/airflow/entityq`, and sets `PYTHONPATH=/opt/airflow/entityq/src`.

## DAG

The runnable DAG is:

- `orchestration/airflow/dags/entityq_quality_pipeline_dag.py`

It runs the reproducible non-Kafka workflow:

1. `python -m entityq.run_pipeline`
2. `python -m entityq.new_dataset_onboarding --dataset counterparty_trade_links`
3. `python -m entityq.sql_quality_runner`
4. `python -m entityq.counterparty_trade_remediation`

Kafka is not part of the default Airflow DAG because it requires a running local broker and is better handled as a separate streaming demo.

## Start Airflow

```bash
cd orchestration/airflow
docker compose up airflow-init
docker compose up -d
docker compose ps
```

Open the UI at `http://localhost:8080`.

If port 8080 is already in use, choose another host port:

```bash
AIRFLOW_WEBSERVER_PORT=8081 docker compose up -d
```

Local demo credentials:

- Username: `airflow`
- Password: `airflow`

Trigger the `entityq_quality_pipeline` DAG manually from the Airflow UI.

## Stop Airflow

```bash
cd orchestration/airflow
docker compose down --volumes --remove-orphans
```

## Generated Files

The following local runtime paths are ignored by git:

- `orchestration/airflow/logs/`
- `orchestration/airflow/postgres-db-data/`
