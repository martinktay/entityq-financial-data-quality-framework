from __future__ import annotations

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AIRFLOW_ROOT = PROJECT_ROOT / "orchestration" / "airflow"


def test_airflow_compose_defines_runnable_local_stack() -> None:
    compose = yaml.safe_load((AIRFLOW_ROOT / "docker-compose.yml").read_text())

    services = compose["services"]

    assert {"airflow-db", "airflow-init", "airflow-webserver", "airflow-scheduler"} <= set(services)
    assert services["airflow-webserver"]["ports"] == ["${AIRFLOW_WEBSERVER_PORT:-8080}:8080"]

    for service_name in ["airflow-init", "airflow-webserver", "airflow-scheduler"]:
        service = services[service_name]
        assert service["build"]["context"] == "../.."
        assert service["build"]["dockerfile"] == "orchestration/airflow/Dockerfile"
        assert "../..:/opt/airflow/entityq" in service["volumes"]
        assert "./dags:/opt/airflow/dags" in service["volumes"]
        assert service["environment"]["PYTHONPATH"] == "/opt/airflow/entityq/src"


def test_airflow_dag_orchestrates_entityq_workflow_without_kafka_tasks() -> None:
    dag_source = (AIRFLOW_ROOT / "dags" / "entityq_quality_pipeline_dag.py").read_text()

    expected_fragments = [
        'dag_id="entityq_quality_pipeline"',
        '"python -m entityq.run_pipeline"',
        '"python -m entityq.new_dataset_onboarding --dataset counterparty_trade_links"',
        '"python -m entityq.sql_quality_runner"',
        '"python -m entityq.counterparty_trade_remediation"',
        "run_core_pipeline >> run_new_dataset_onboarding >> run_sql_quality_checks >> run_remediation_workflow",
    ]

    for fragment in expected_fragments:
        assert fragment in dag_source

    assert "kafka_provider_producer" not in dag_source
    assert "kafka_provider_consumer" not in dag_source


def test_airflow_dockerfile_installs_project_dependencies_as_airflow_user() -> None:
    dockerfile = (AIRFLOW_ROOT / "Dockerfile").read_text()

    assert "FROM apache/airflow:2.9.3-python3.11" in dockerfile
    assert "USER airflow" in dockerfile
    assert "COPY --chown=airflow:0 orchestration/airflow/requirements-airflow.txt" in dockerfile
    assert "COPY requirements.txt" not in dockerfile
    assert "pip install --no-cache-dir" in dockerfile
    assert dockerfile.index("USER airflow") < dockerfile.index("pip install --no-cache-dir")
    assert "ENV PYTHONPATH=/opt/airflow/entityq/src" in dockerfile


def test_airflow_requirements_are_limited_to_dag_runtime_dependencies() -> None:
    requirements = (AIRFLOW_ROOT / "requirements-airflow.txt").read_text()

    for package in ["pandas", "numpy", "scikit-learn", "duckdb", "tabulate", "pyyaml"]:
        assert package in requirements

    for package in ["apache-airflow", "streamlit", "dbt-core", "dbt-duckdb", "fastapi", "confluent-kafka"]:
        assert package not in requirements
