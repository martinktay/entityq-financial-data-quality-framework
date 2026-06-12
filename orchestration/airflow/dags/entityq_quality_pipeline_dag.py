from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


ENTITYQ_ROOT = "/opt/airflow/entityq"
PYTHONPATH = "/opt/airflow/entityq/src"


def create_task(task_id: str, command: str) -> BashOperator:
    """
    Create a BashOperator task that runs one EntityQ workflow command.
    """
    return BashOperator(
        task_id=task_id,
        bash_command=f"cd {ENTITYQ_ROOT} && {command}",
        env={"PYTHONPATH": PYTHONPATH},
    )


with DAG(
    dag_id="entityq_quality_pipeline",
    description=(
        "Orchestrates the core EntityQ pipeline, counterparty onboarding, SQL "
        "quality checks, and remediation workflows."
    ),
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["entityq", "quality", "demo"],
) as dag:
    run_core_pipeline = create_task(
        "run_core_pipeline",
        "python -m entityq.run_pipeline",
    )

    run_new_dataset_onboarding = create_task(
        "run_new_dataset_onboarding",
        "python -m entityq.new_dataset_onboarding --dataset counterparty_trade_links",
    )

    run_sql_quality_checks = create_task(
        "run_sql_quality_checks",
        "python -m entityq.sql_quality_runner",
    )

    run_remediation_workflow = create_task(
        "run_remediation_workflow",
        "python -m entityq.counterparty_trade_remediation",
    )

    # Kafka remains a separate streaming demo because it needs a running broker.
    run_core_pipeline >> run_new_dataset_onboarding >> run_sql_quality_checks >> run_remediation_workflow
