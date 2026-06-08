from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INCOMING_DATA_PATH = PROJECT_ROOT / "data" / "incoming" / "counterparty_trade_links.csv"
SQL_CHECKS_PATH = PROJECT_ROOT / "sql" / "counterparty_trade_quality_checks.sql"
QUALITY_REPORT_DIR = PROJECT_ROOT / "data" / "quality_reports"

TABLE_NAME = "counterparty_trade_links"


def read_sql_file(sql_path: Path = SQL_CHECKS_PATH) -> str:
    """
    Read the SQL quality check file.
    """
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL checks file not found: {sql_path}")

    return sql_path.read_text(encoding="utf-8")


def parse_sql_rules(sql_text: str) -> list[dict[str, str]]:
    """
    Parse SQL rules from a single SQL file.

    Each rule must contain metadata comments before the SELECT statement:

    -- RULE_ID: SQL_TRADE_001
    -- SEVERITY: Critical
    -- DIMENSION: Completeness
    -- DESCRIPTION: Trade ID must not be missing.
    -- RECOMMENDATION: Ensure every trade-linked record has a trade identifier.
    select ...
    """
    pattern = re.compile(
        r"-- RULE_ID:\s*(?P<rule_id>.+?)\n"
        r"-- SEVERITY:\s*(?P<severity>.+?)\n"
        r"-- DIMENSION:\s*(?P<dimension>.+?)\n"
        r"-- DESCRIPTION:\s*(?P<description>.+?)\n"
        r"-- RECOMMENDATION:\s*(?P<recommendation>.+?)\n"
        r"(?P<query>select.*?;)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    rules: list[dict[str, str]] = []

    for match in pattern.finditer(sql_text):
        rules.append(
            {
                "rule_id": match.group("rule_id").strip(),
                "severity": match.group("severity").strip(),
                "dimension": match.group("dimension").strip(),
                "description": match.group("description").strip(),
                "recommendation": match.group("recommendation").strip(),
                "query": match.group("query").strip(),
            }
        )

    if not rules:
        raise ValueError(
            "No SQL rules were parsed. Check that every rule has RULE_ID, "
            "SEVERITY, DIMENSION, DESCRIPTION, RECOMMENDATION and a SELECT query."
        )

    return rules


def create_duckdb_connection(csv_path: Path = INCOMING_DATA_PATH) -> duckdb.DuckDBPyConnection:
    """
    Create an in-memory DuckDB connection and register the incoming CSV as a table.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Incoming dataset not found: {csv_path}. "
            "Place counterparty_trade_links.csv inside data/incoming."
        )

    connection = duckdb.connect(database=":memory:")

    connection.execute(
        f"""
        create or replace table {TABLE_NAME} as
        select *
        from read_csv_auto('{csv_path.as_posix()}', header=true, ignore_errors=true);
        """
    )

    return connection


def run_sql_rules(
    connection: duckdb.DuckDBPyConnection,
    rules: list[dict[str, str]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute parsed SQL rules and return rule-level and failed-record outputs.
    """
    total_rows = connection.execute(f"select count(*) from {TABLE_NAME}").fetchone()[0]

    rule_result_rows: list[dict[str, Any]] = []
    failed_record_frames: list[pd.DataFrame] = []

    for rule in rules:
        rule_id = rule["rule_id"]
        query = rule["query"]

        try:
            failed_records = connection.execute(query).fetchdf()
            failed_count = len(failed_records)
            status = "failed" if failed_count > 0 else "passed"
            error_message = ""

            if failed_count > 0:
                failed_records.insert(0, "rule_id", rule_id)
                failed_records.insert(1, "severity", rule["severity"])
                failed_records.insert(2, "dimension", rule["dimension"])
                failed_records.insert(3, "issue_type", rule["description"])
                failed_record_frames.append(failed_records)

        except Exception as exc:
            failed_count = total_rows
            status = "error"
            error_message = str(exc)

        rule_result_rows.append(
            {
                "dataset_name": TABLE_NAME,
                "rule_id": rule_id,
                "severity": rule["severity"],
                "dimension": rule["dimension"],
                "description": rule["description"],
                "recommendation": rule["recommendation"],
                "total_rows": total_rows,
                "failed_count": failed_count,
                "failure_rate_pct": round((failed_count / total_rows) * 100, 2)
                if total_rows
                else 0,
                "status": status,
                "error_message": error_message,
                "validated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    rule_results = pd.DataFrame(rule_result_rows)

    if failed_record_frames:
        failed_records_all = pd.concat(
            failed_record_frames,
            ignore_index=True,
            sort=False,
        )
    else:
        failed_records_all = pd.DataFrame()

    return rule_results, failed_records_all


def create_sql_stakeholder_report(
    rule_results: pd.DataFrame,
    failed_records: pd.DataFrame,
) -> str:
    """
    Create a markdown report summarising SQL quality check results.
    """
    rules_executed = len(rule_results)
    rules_with_failures = int((rule_results["failed_count"] > 0).sum())
    total_failed_records = len(failed_records)

    critical_failures = rule_results[
        (rule_results["severity"] == "Critical") & (rule_results["failed_count"] > 0)
    ]

    high_failures = rule_results[
        (rule_results["severity"] == "High") & (rule_results["failed_count"] > 0)
    ]

    top_failures = (
        rule_results.sort_values("failed_count", ascending=False)
        .head(10)
        .loc[
            :,
            [
                "rule_id",
                "severity",
                "dimension",
                "description",
                "failed_count",
                "failure_rate_pct",
            ],
        ]
    )

    report_lines = [
        "# SQL Data Quality Report: counterparty_trade_links",
        "",
        "## Executive Summary",
        "",
        f"- SQL rules executed: {rules_executed:,}",
        f"- Rules with failures: {rules_with_failures:,}",
        f"- Failed record exceptions generated: {total_failed_records:,}",
        f"- Critical rules with failures: {len(critical_failures):,}",
        f"- High-severity rules with failures: {len(high_failures):,}",
        "",
        "## Why This Matters",
        "",
        (
            "This SQL layer demonstrates how EntityQ can validate a newly onboarded "
            "dirty financial dataset using transparent SQL checks. The dataset links "
            "trades to counterparties, issuers, instruments, KYC status, provider "
            "confidence scores and reference data attributes. These checks help identify "
            "issues that could affect client onboarding, compliance, settlement, "
            "counterparty risk, issuer classification and reporting workflows."
        ),
        "",
        "## Top SQL Rule Failures",
        "",
        top_failures.to_markdown(index=False),
        "",
        "## Outputs",
        "",
        "- data/quality_reports/sql_counterparty_trade_rule_results.csv",
        "- data/quality_reports/sql_counterparty_trade_failed_records.csv",
        "- data/quality_reports/sql_counterparty_trade_report.md",
        "",
    ]

    return "\n".join(report_lines)


def run_sql_quality_checks() -> None:
    """
    Execute SQL quality checks against the incoming counterparty trade dataset.
    """
    QUALITY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    sql_text = read_sql_file()
    rules = parse_sql_rules(sql_text)

    connection = create_duckdb_connection()

    try:
        rule_results, failed_records = run_sql_rules(connection, rules)
    finally:
        connection.close()

    report = create_sql_stakeholder_report(rule_results, failed_records)

    rule_results_path = QUALITY_REPORT_DIR / "sql_counterparty_trade_rule_results.csv"
    failed_records_path = QUALITY_REPORT_DIR / "sql_counterparty_trade_failed_records.csv"
    report_path = QUALITY_REPORT_DIR / "sql_counterparty_trade_report.md"

    rule_results.to_csv(rule_results_path, index=False)
    failed_records.to_csv(failed_records_path, index=False)
    report_path.write_text(report, encoding="utf-8")

    print("SQL quality checks completed.")
    print(f"Rules executed: {len(rule_results):,}")
    print(f"Rules with failures: {(rule_results['failed_count'] > 0).sum():,}")
    print(f"Failed record exceptions: {len(failed_records):,}")
    print("")
    print("Reports written to:")
    print(f"- {rule_results_path}")
    print(f"- {failed_records_path}")
    print(f"- {report_path}")


if __name__ == "__main__":
    run_sql_quality_checks()