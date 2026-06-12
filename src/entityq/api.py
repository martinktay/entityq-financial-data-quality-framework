from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
from fastapi import FastAPI, HTTPException, Query


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUALITY_REPORT_DIR = PROJECT_ROOT / "data" / "quality_reports"
DUCKDB_PATH = PROJECT_ROOT / "data" / "processed" / "entityq.duckdb"
CURATED_DIR = PROJECT_ROOT / "data" / "curated"

app = FastAPI(
    title="EntityQ Data Quality API",
    description=(
        "API for exposing financial entity data quality summaries, "
        "failed rules, anomaly candidates and dbt/DuckDB quality marts."
    ),
    version="1.0.0",
)


def read_csv_report(file_name: str) -> pd.DataFrame:
    """
    Read a CSV report from the quality_reports directory.

    This keeps API endpoints simple and ensures they all read from the same
    trusted pipeline outputs.
    """
    file_path = QUALITY_REPORT_DIR / file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"{file_name} was not found. "
                "Run `python -m entityq.run_pipeline` first."
            ),
        )

    return pd.read_csv(file_path)


def read_text_report(file_name: str) -> str:
    """
    Read a markdown or text report from the quality_reports directory.
    """
    file_path = QUALITY_REPORT_DIR / file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"{file_name} was not found. "
                "Run `python -m entityq.run_full_demo` first."
            ),
        )

    return file_path.read_text(encoding="utf-8")


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Convert a dataframe into JSON-friendly records.

    Pandas can contain NaN values, which are not valid JSON.
    Replacing them with None makes the API response safer.
    """
    cleaned = df.where(pd.notnull(df), None)
    return cleaned.to_dict(orient="records")


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.

    This confirms the API is running.
    """
    return {"status": "ok", "service": "EntityQ Data Quality API"}


@app.get("/quality/summary")
def get_table_quality_summary() -> list[dict[str, Any]]:
    """
    Return table-level data quality summary.

    Source file:
    data/quality_reports/table_quality_summary.csv
    """
    df = read_csv_report("table_quality_summary.csv")
    return dataframe_to_records(df)


@app.get("/quality/scorecard")
def get_quality_scorecard() -> list[dict[str, Any]]:
    """
    Return quality scores by table and data quality dimension.

    Source file:
    data/quality_reports/quality_scorecard.csv
    """
    df = read_csv_report("quality_scorecard.csv")
    return dataframe_to_records(df)


@app.get("/quality/failed-rules")
def get_failed_rules(
    severity: str | None = Query(
        default=None,
        description="Optional severity filter, e.g. Critical, High, Medium.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of failed rules to return.",
    ),
) -> list[dict[str, Any]]:
    """
    Return failed data quality rules.

    Optional:
    - Filter by severity.
    - Limit the number of results.
    """
    df = read_csv_report("rule_results.csv")

    failed = df[df["failed_count"] > 0].copy()

    if severity:
        failed = failed[
            failed["severity"].str.lower() == severity.lower()
        ]

    failed = failed.sort_values("failed_count", ascending=False).head(limit)

    return dataframe_to_records(failed)


@app.get("/quality/anomalies")
def get_entity_anomalies(
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of anomaly candidates to return.",
    ),
) -> list[dict[str, Any]]:
    """
    Return AI/ML anomaly candidates.

    Source file:
    data/quality_reports/entity_anomalies.csv
    """
    df = read_csv_report("entity_anomalies.csv")

    if "anomaly_score" in df.columns:
        df = df.sort_values("anomaly_score", ascending=True)

    return dataframe_to_records(df.head(limit))


@app.get("/quality/stakeholder-report")
def get_stakeholder_report() -> dict[str, str]:
    """
    Return the stakeholder markdown report as text.
    """
    return {"report": read_text_report("stakeholder_report.md")}


@app.get("/counterparty/rule-results")
def get_counterparty_rule_results() -> list[dict[str, Any]]:
    """
    Return the counterparty onboarding rule results.
    """
    df = read_csv_report("counterparty_trade_links_rule_results.csv")
    return dataframe_to_records(df)


@app.get("/counterparty/failed-records")
def get_counterparty_failed_records() -> list[dict[str, Any]]:
    """
    Return the counterparty onboarding failed records.
    """
    df = read_csv_report("counterparty_trade_links_failed_records.csv")
    return dataframe_to_records(df)


@app.get("/counterparty/sql-rule-results")
def get_counterparty_sql_rule_results() -> list[dict[str, Any]]:
    """
    Return the counterparty SQL rule results.
    """
    df = read_csv_report("sql_counterparty_trade_rule_results.csv")
    return dataframe_to_records(df)


@app.get("/counterparty/remediation-summary")
def get_counterparty_remediation_summary() -> dict[str, str]:
    """
    Return the counterparty remediation markdown summary.
    """
    return {
        "report": read_text_report("counterparty_trade_links_remediation_summary.md")
    }


@app.get("/counterparty/curated-records")
def get_counterparty_curated_records() -> list[dict[str, Any]]:
    """
    Return the curated counterparty records.
    """
    file_path = CURATED_DIR / "counterparty_trade_links_curated.csv"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "counterparty_trade_links_curated.csv was not found. "
                "Run `python -m entityq.run_full_demo` first."
            ),
        )

    return dataframe_to_records(pd.read_csv(file_path))


@app.get("/counterparty/quarantine-records")
def get_counterparty_quarantine_records() -> list[dict[str, Any]]:
    """
    Return the quarantined counterparty records.
    """
    file_path = CURATED_DIR / "counterparty_trade_links_quarantine.csv"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "counterparty_trade_links_quarantine.csv was not found. "
                "Run `python -m entityq.run_full_demo` first."
            ),
        )

    return dataframe_to_records(pd.read_csv(file_path))


@app.get("/dbt/entity-quality-summary")
def get_dbt_entity_quality_summary() -> list[dict[str, Any]]:
    """
    Return the dbt/DuckDB mart for entity quality summary.

    Source table:
    mart_entity_quality_summary
    """
    if not DUCKDB_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "DuckDB database was not found. "
                "Run dbt from dbt/entityq using `dbt run --profiles-dir .` first."
            ),
        )

    query = "select * from mart_entity_quality_summary"

    try:
        with duckdb.connect(str(DUCKDB_PATH), read_only=True) as connection:
            df = connection.execute(query).fetchdf()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read DuckDB mart: {exc}",
        ) from exc

    return dataframe_to_records(df)