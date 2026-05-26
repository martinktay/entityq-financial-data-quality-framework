from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "quality_reports"


def prepare_python_path() -> None:
    """
    Make sure Airflow can import the local entityq package.

    In local development, the project is usually installed with:

    pip install -e .

    This sys.path fallback also helps Airflow find the src/entityq package
    if the package has not been installed inside the Airflow environment.
    """
    src_path = str(SRC_DIR)

    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    os.chdir(PROJECT_ROOT)


def generate_synthetic_data() -> None:
    """
    Airflow task 1:
    Generate synthetic messy financial entity data.
    """
    prepare_python_path()

    from entityq.data_generation import generate_all

    generate_all(RAW_DIR, entity_count=5000)


def profile_raw_data() -> None:
    """
    Airflow task 2:
    Profile the generated raw datasets.
    """
    prepare_python_path()

    from entityq.profiling import run_profiling

    run_profiling(RAW_DIR, REPORT_DIR)


def validate_data_quality_rules() -> None:
    """
    Airflow task 3:
    Run rule-based data quality validation checks.
    """
    prepare_python_path()

    from entityq.validation import run_validation

    run_validation(RAW_DIR, REPORT_DIR)


def create_quality_scorecards() -> None:
    """
    Airflow task 4:
    Convert rule-level validation results into quality scorecards.
    """
    prepare_python_path()

    from entityq.metrics import run_metrics

    run_metrics(output_dir=REPORT_DIR)


def run_entity_anomaly_detection() -> None:
    """
    Airflow task 5:
    Run AI/ML-enabled anomaly detection on entity records.
    """
    prepare_python_path()

    from entityq.anomaly_detection import run_anomaly_detection

    run_anomaly_detection(RAW_DIR, REPORT_DIR)


def create_stakeholder_quality_report() -> None:
    """
    Airflow task 6:
    Create the stakeholder-facing markdown report.
    """
    prepare_python_path()

    from entityq.reporting import create_stakeholder_report

    create_stakeholder_report(REPORT_DIR)


default_args = {
    "owner": "entityq",
    "depends_on_past": False,
    "retries": 0,
}


with DAG(
    dag_id="entityq_financial_entity_quality_pipeline",
    description="EntityQ financial entity data quality and automation pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["data-quality", "entity-data", "reference-data", "automation"],
) as dag:
    generate_data_task = PythonOperator(
        task_id="generate_synthetic_data",
        python_callable=generate_synthetic_data,
    )

    profile_data_task = PythonOperator(
        task_id="profile_raw_data",
        python_callable=profile_raw_data,
    )

    validate_rules_task = PythonOperator(
        task_id="validate_data_quality_rules",
        python_callable=validate_data_quality_rules,
    )

    create_scorecards_task = PythonOperator(
        task_id="create_quality_scorecards",
        python_callable=create_quality_scorecards,
    )

    anomaly_detection_task = PythonOperator(
        task_id="run_entity_anomaly_detection",
        python_callable=run_entity_anomaly_detection,
    )

    stakeholder_report_task = PythonOperator(
        task_id="create_stakeholder_quality_report",
        python_callable=create_stakeholder_quality_report,
    )

    (
        generate_data_task
        >> profile_data_task
        >> validate_rules_task
        >> create_scorecards_task
        >> anomaly_detection_task
        >> stakeholder_report_task
    )