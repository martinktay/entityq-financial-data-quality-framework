from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "config" / "dataset_registry.yml"
QUALITY_REPORT_DIR = PROJECT_ROOT / "data" / "quality_reports"


def load_registry() -> dict[str, Any]:
    """
    Load dataset registry configuration.

    The registry describes new datasets that can be onboarded into the
    EntityQ framework without rewriting the whole pipeline.
    """
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"Dataset registry not found at {REGISTRY_PATH}. "
            "Create config/dataset_registry.yml first."
        )

    with REGISTRY_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_dataset_config(dataset_name: str) -> dict[str, Any]:
    """
    Return the configuration for a named dataset.
    """
    registry = load_registry()
    datasets = registry.get("datasets", {})

    if dataset_name not in datasets:
        available = ", ".join(datasets.keys())
        raise ValueError(
            f"Dataset '{dataset_name}' is not registered. "
            f"Available datasets: {available}"
        )

    return datasets[dataset_name]


def read_dataset(dataset_config: dict[str, Any]) -> pd.DataFrame:
    """
    Read a registered dataset from disk.
    """
    file_path = PROJECT_ROOT / dataset_config["file_path"]

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found at {file_path}. "
            "Confirm the CSV has been placed in data/incoming."
        )

    return pd.read_csv(file_path)


def clean_string_series(series: pd.Series) -> pd.Series:
    """
    Normalise a string-like pandas series for quality checks.
    """
    return series.fillna("").astype(str).str.strip()


def create_column_profile(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Create a column-level profile showing missing values, distinct values,
    inferred data type and sample values.
    """
    profile_rows: list[dict[str, Any]] = []
    total_rows = len(df)

    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        blank_count = int((clean_string_series(df[column]) == "").sum())
        distinct_count = int(df[column].nunique(dropna=True))

        sample_values = (
            df[column]
            .dropna()
            .astype(str)
            .head(5)
            .tolist()
        )

        profile_rows.append(
            {
                "dataset_name": dataset_name,
                "column_name": column,
                "dtype": str(df[column].dtype),
                "total_rows": total_rows,
                "missing_count": missing_count,
                "blank_count": blank_count,
                "missing_or_blank_count": missing_count + blank_count,
                "missing_or_blank_pct": round(
                    ((missing_count + blank_count) / total_rows) * 100,
                    2,
                )
                if total_rows
                else 0,
                "distinct_count": distinct_count,
                "sample_values": " | ".join(sample_values),
            }
        )

    return pd.DataFrame(profile_rows)


def add_failed_records(
    failed_records: list[dict[str, Any]],
    df: pd.DataFrame,
    mask: pd.Series,
    rule_id: str,
    issue_type: str,
    severity: str,
    primary_key: str,
    columns_to_include: list[str],
) -> None:
    """
    Append failed records for a validation rule to a shared list.

    This creates a row-level exception file that analysts can use for
    remediation and root-cause investigation.
    """
    if mask.empty:
        return

    safe_mask = mask.fillna(False)
    failed = df.loc[safe_mask].copy()

    for _, row in failed.iterrows():
        record: dict[str, Any] = {
            "rule_id": rule_id,
            "issue_type": issue_type,
            "severity": severity,
            "record_id": row.get(primary_key, None),
        }

        for column in columns_to_include:
            if column in df.columns:
                record[column] = row.get(column, None)

        failed_records.append(record)


def create_rule_result(
    dataset_name: str,
    rule_id: str,
    dimension: str,
    severity: str,
    description: str,
    failed_count: int,
    total_rows: int,
    recommendation: str,
) -> dict[str, Any]:
    """
    Create a rule-level validation result.
    """
    return {
        "dataset_name": dataset_name,
        "rule_id": rule_id,
        "dimension": dimension,
        "severity": severity,
        "description": description,
        "total_rows": total_rows,
        "failed_count": failed_count,
        "failure_rate_pct": round((failed_count / total_rows) * 100, 2)
        if total_rows
        else 0,
        "recommendation": recommendation,
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }


def validate_counterparty_trade_links(
    df: pd.DataFrame,
    dataset_name: str,
    dataset_config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate the counterparty_trade_links dataset.

    These rules simulate checks relevant to financial data workflows where
    trade records depend on accurate entity, issuer, KYC and reference data.
    """
    total_rows = len(df)
    primary_key = dataset_config["primary_key"]
    allowed_values = dataset_config.get("allowed_values", {})

    rule_results: list[dict[str, Any]] = []
    failed_records: list[dict[str, Any]] = []

    required_columns = dataset_config.get("required_columns", [])
    missing_columns = [column for column in required_columns if column not in df.columns]

    rule_results.append(
        create_rule_result(
            dataset_name=dataset_name,
            rule_id="SCHEMA_001",
            dimension="Schema",
            severity="Critical",
            description="Required columns must exist in the incoming dataset.",
            failed_count=len(missing_columns),
            total_rows=len(required_columns),
            recommendation=(
                "Add missing columns to the source feed or update the dataset registry "
                "if the schema has intentionally changed. Missing columns: "
                + ", ".join(missing_columns)
                if missing_columns
                else "Schema contains all required columns."
            ),
        )
    )

    if missing_columns:
        return pd.DataFrame(rule_results), pd.DataFrame(failed_records)

    trade_id = clean_string_series(df["trade_id"])
    counterparty_entity_id = clean_string_series(df["counterparty_entity_id"])
    issuer_id = clean_string_series(df["issuer_id"])
    counterparty_name = clean_string_series(df["counterparty_name"])

    trade_date = pd.to_datetime(df["trade_date"], errors="coerce")
    settlement_date = pd.to_datetime(df["settlement_date"], errors="coerce")
    last_verified_date = pd.to_datetime(df["last_verified_date"], errors="coerce")

    notional_amount = pd.to_numeric(df["notional_amount"], errors="coerce")
    provider_confidence_score = pd.to_numeric(
        df["provider_confidence_score"],
        errors="coerce",
    )

    current_date = pd.Timestamp.now(tz="UTC").tz_localize(None)

    # Rule 1: missing trade ID
    mask = trade_id == ""
    rule_results.append(
        create_rule_result(
            dataset_name,
            "TRADE_001",
            "Completeness",
            "Critical",
            "Trade ID must not be missing.",
            int(mask.sum()),
            total_rows,
            "Ensure every trade-linked record has a unique trade identifier.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "TRADE_001",
        "Missing trade ID",
        "Critical",
        primary_key,
        ["trade_id", "source_system", "provider_name"],
    )

    # Rule 2: duplicate trade IDs
    mask = trade_id.ne("") & trade_id.duplicated(keep=False)
    rule_results.append(
        create_rule_result(
            dataset_name,
            "TRADE_002",
            "Uniqueness",
            "Critical",
            "Trade ID must be unique.",
            int(mask.sum()),
            total_rows,
            "Investigate duplicate trade identifiers across source systems.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "TRADE_002",
        "Duplicate trade ID",
        "Critical",
        primary_key,
        ["trade_id", "counterparty_entity_id", "issuer_id", "source_system"],
    )

    # Rule 3: missing counterparty entity reference
    mask = counterparty_entity_id == ""
    rule_results.append(
        create_rule_result(
            dataset_name,
            "CP_001",
            "Completeness",
            "High",
            "Counterparty entity ID must not be missing.",
            int(mask.sum()),
            total_rows,
            "Map each trade to a valid counterparty entity master record.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "CP_001",
        "Missing counterparty entity ID",
        "High",
        primary_key,
        ["trade_id", "counterparty_entity_id", "counterparty_name", "source_system"],
    )

    # Rule 4: weak or missing counterparty name
    mask = counterparty_name.isin(["", "Unknown Counterparty"])
    rule_results.append(
        create_rule_result(
            dataset_name,
            "CP_002",
            "Completeness",
            "Medium",
            "Counterparty name should be populated and meaningful.",
            int(mask.sum()),
            total_rows,
            "Enrich weak counterparty names from trusted reference data sources.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "CP_002",
        "Missing or weak counterparty name",
        "Medium",
        primary_key,
        ["trade_id", "counterparty_entity_id", "counterparty_name"],
    )

    # Rule 5: missing issuer ID
    mask = issuer_id == ""
    rule_results.append(
        create_rule_result(
            dataset_name,
            "ISSUER_001",
            "Completeness",
            "High",
            "Issuer ID must not be missing.",
            int(mask.sum()),
            total_rows,
            "Ensure each instrument is linked to an issuer reference record.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "ISSUER_001",
        "Missing issuer ID",
        "High",
        primary_key,
        ["trade_id", "issuer_id", "issuer_name", "instrument_type"],
    )

    # Rule 6: orphan issuer IDs
    mask = issuer_id.str.startswith("ISS-ORPHAN")
    rule_results.append(
        create_rule_result(
            dataset_name,
            "ISSUER_002",
            "Referential Integrity",
            "High",
            "Issuer ID should resolve to a known issuer reference record.",
            int(mask.sum()),
            total_rows,
            "Investigate issuer records not found in the issuer master dataset.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "ISSUER_002",
        "Orphan issuer reference",
        "High",
        primary_key,
        ["trade_id", "issuer_id", "issuer_name", "source_system"],
    )

    # Rule 7: invalid trade date
    mask = trade_date.isna()
    rule_results.append(
        create_rule_result(
            dataset_name,
            "DATE_001",
            "Validity",
            "High",
            "Trade date must be a valid date.",
            int(mask.sum()),
            total_rows,
            "Fix invalid trade date values before downstream processing.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "DATE_001",
        "Invalid trade date",
        "High",
        primary_key,
        ["trade_id", "trade_date", "settlement_date"],
    )

    # Rule 8: settlement date before trade date
    mask = trade_date.notna() & settlement_date.notna() & (settlement_date < trade_date)
    rule_results.append(
        create_rule_result(
            dataset_name,
            "DATE_002",
            "Validity",
            "High",
            "Settlement date should not be before trade date.",
            int(mask.sum()),
            total_rows,
            "Review settlement-date calculation and source-system date mappings.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "DATE_002",
        "Settlement date before trade date",
        "High",
        primary_key,
        ["trade_id", "trade_date", "settlement_date", "source_system"],
    )

    # Rule 9: invalid notional amount
    mask = notional_amount.isna() | (notional_amount <= 0)
    rule_results.append(
        create_rule_result(
            dataset_name,
            "AMOUNT_001",
            "Validity",
            "High",
            "Notional amount must be numeric and greater than zero.",
            int(mask.sum()),
            total_rows,
            "Correct missing, non-numeric or negative notional values.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "AMOUNT_001",
        "Invalid notional amount",
        "High",
        primary_key,
        ["trade_id", "notional_amount", "currency"],
    )

    # Rule 10: invalid currency
    allowed_currencies = set(allowed_values.get("currency", []))
    mask = ~clean_string_series(df["currency"]).isin(allowed_currencies)
    rule_results.append(
        create_rule_result(
            dataset_name,
            "REF_001",
            "Validity",
            "High",
            "Currency must be an approved ISO-style currency code.",
            int(mask.sum()),
            total_rows,
            "Standardise currency codes before downstream risk and reporting use.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "REF_001",
        "Invalid currency",
        "High",
        primary_key,
        ["trade_id", "currency", "notional_amount"],
    )

    # Rule 11: invalid risk country
    allowed_countries = set(allowed_values.get("country_code", []))
    mask = ~clean_string_series(df["risk_country"]).isin(allowed_countries)
    rule_results.append(
        create_rule_result(
            dataset_name,
            "REF_002",
            "Validity",
            "High",
            "Risk country must be a valid supported country code.",
            int(mask.sum()),
            total_rows,
            "Map invalid risk-country values to controlled reference data.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "REF_002",
        "Invalid risk country",
        "High",
        primary_key,
        ["trade_id", "counterparty_entity_id", "risk_country"],
    )

    # Rule 12: invalid instrument type
    allowed_instruments = set(allowed_values.get("instrument_type", []))
    mask = ~clean_string_series(df["instrument_type"]).isin(allowed_instruments)
    rule_results.append(
        create_rule_result(
            dataset_name,
            "REF_003",
            "Validity",
            "Medium",
            "Instrument type must be in the approved instrument taxonomy.",
            int(mask.sum()),
            total_rows,
            "Standardise instrument classification values.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "REF_003",
        "Invalid instrument type",
        "Medium",
        primary_key,
        ["trade_id", "instrument_type", "instrument_id"],
    )

    # Rule 13: high-risk counterparty with incomplete KYC
    mask = (
        clean_string_series(df["counterparty_risk_rating"]).eq("High")
        & ~clean_string_series(df["kyc_status"]).eq("Approved")
    )
    rule_results.append(
        create_rule_result(
            dataset_name,
            "KYC_001",
            "Compliance",
            "Critical",
            "High-risk counterparties should have approved KYC.",
            int(mask.sum()),
            total_rows,
            "Prioritise remediation of high-risk counterparties with incomplete KYC.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "KYC_001",
        "High-risk counterparty with incomplete KYC",
        "Critical",
        primary_key,
        [
            "trade_id",
            "counterparty_entity_id",
            "kyc_status",
            "counterparty_risk_rating",
            "notional_amount",
            "currency",
        ],
    )

    # Rule 14: invalid provider confidence score
    mask = (
        provider_confidence_score.isna()
        | (provider_confidence_score < 0)
        | (provider_confidence_score > 1)
    )
    rule_results.append(
        create_rule_result(
            dataset_name,
            "PROVIDER_001",
            "Validity",
            "High",
            "Provider confidence score must be between 0 and 1.",
            int(mask.sum()),
            total_rows,
            "Review provider scoring feed and reject invalid scores.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "PROVIDER_001",
        "Invalid provider confidence score",
        "High",
        primary_key,
        ["trade_id", "provider_name", "provider_confidence_score"],
    )

    # Rule 15: low provider confidence score
    mask = provider_confidence_score.notna() & (provider_confidence_score >= 0) & (
        provider_confidence_score < 0.70
    )
    rule_results.append(
        create_rule_result(
            dataset_name,
            "PROVIDER_002",
            "Accuracy",
            "Medium",
            "Provider confidence score should not be below 0.70.",
            int(mask.sum()),
            total_rows,
            "Route low-confidence provider records for review or enrichment.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "PROVIDER_002",
        "Low provider confidence score",
        "Medium",
        primary_key,
        ["trade_id", "provider_name", "provider_confidence_score"],
    )

    # Rule 16: invalid ISIN
    isin = clean_string_series(df["isin"])
    mask = ~isin.str.match(r"^[A-Z]{2}[A-Z0-9]{10}$", na=False)
    rule_results.append(
        create_rule_result(
            dataset_name,
            "SECURITY_001",
            "Validity",
            "Medium",
            "ISIN should follow a 12-character security identifier pattern.",
            int(mask.sum()),
            total_rows,
            "Validate security identifiers against trusted instrument reference data.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "SECURITY_001",
        "Invalid ISIN pattern",
        "Medium",
        primary_key,
        ["trade_id", "issuer_id", "isin"],
    )

    # Rule 17: invalid LEI
    lei = clean_string_series(df["lei"])
    mask = ~lei.str.match(r"^[A-Z0-9]{20}$", na=False)
    rule_results.append(
        create_rule_result(
            dataset_name,
            "ENTITY_001",
            "Validity",
            "Medium",
            "LEI should follow a 20-character alphanumeric pattern.",
            int(mask.sum()),
            total_rows,
            "Enrich or correct invalid legal entity identifiers.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "ENTITY_001",
        "Invalid LEI pattern",
        "Medium",
        primary_key,
        ["trade_id", "counterparty_entity_id", "lei"],
    )

    # Rule 18: stale reference verification
    mask = last_verified_date.notna() & (
        last_verified_date < current_date - pd.Timedelta(days=365)
    )
    rule_results.append(
        create_rule_result(
            dataset_name,
            "TIME_001",
            "Timeliness",
            "Medium",
            "Reference data should be verified within the last 365 days.",
            int(mask.sum()),
            total_rows,
            "Refresh stale counterparty and issuer reference records.",
        )
    )
    add_failed_records(
        failed_records,
        df,
        mask,
        "TIME_001",
        "Stale reference verification",
        "Medium",
        primary_key,
        ["trade_id", "counterparty_entity_id", "last_verified_date"],
    )

    return pd.DataFrame(rule_results), pd.DataFrame(failed_records)


def create_stakeholder_report(
    dataset_name: str,
    df: pd.DataFrame,
    column_profile: pd.DataFrame,
    rule_results: pd.DataFrame,
    failed_records: pd.DataFrame,
) -> str:
    """
    Create a stakeholder-readable markdown report for the onboarded dataset.
    """
    total_rows = len(df)
    total_columns = len(df.columns)
    total_failed_rules = int((rule_results["failed_count"] > 0).sum())
    total_failed_records = len(failed_records)

    critical_issues = rule_results[
        (rule_results["severity"] == "Critical") & (rule_results["failed_count"] > 0)
    ]

    high_issues = rule_results[
        (rule_results["severity"] == "High") & (rule_results["failed_count"] > 0)
    ]

    top_rules = (
        rule_results.sort_values("failed_count", ascending=False)
        .head(10)
        .loc[:, ["rule_id", "severity", "description", "failed_count", "failure_rate_pct"]]
    )

    report_lines = [
        f"# New Dataset Onboarding Report: {dataset_name}",
        "",
        "## Executive Summary",
        "",
        f"- Total rows profiled: {total_rows:,}",
        f"- Total columns profiled: {total_columns:,}",
        f"- Validation rules executed: {len(rule_results):,}",
        f"- Rules with failures: {total_failed_rules:,}",
        f"- Failed record exceptions generated: {total_failed_records:,}",
        f"- Critical rules with failures: {len(critical_issues):,}",
        f"- High-severity rules with failures: {len(high_issues):,}",
        "",
        "## What This Dataset Represents",
        "",
        (
            "This dataset simulates trade-linked counterparty reference data. "
            "It connects trade records to counterparties, issuers, instruments, "
            "KYC status, risk ratings, provider confidence scores and source systems. "
            "This is useful for demonstrating how poor entity/reference data can affect "
            "financial workflows such as client onboarding, KYC, counterparty risk, "
            "issuer classification, settlement and reporting."
        ),
        "",
        "## Top Data Quality Issues",
        "",
        top_rules.to_markdown(index=False),
        "",
        "## Recommended Actions",
        "",
        "1. Prioritise critical issues such as duplicate trade IDs and high-risk counterparties with incomplete KYC.",
        "2. Route invalid issuer and counterparty references to reference data remediation queues.",
        "3. Standardise invalid currency, country and instrument taxonomy values.",
        "4. Review low-confidence provider records before using them in curated data products.",
        "5. Refresh stale reference records older than 365 days.",
        "",
        "## Output Files",
        "",
        f"- data/quality_reports/{dataset_name}_column_profile.csv",
        f"- data/quality_reports/{dataset_name}_rule_results.csv",
        f"- data/quality_reports/{dataset_name}_failed_records.csv",
        f"- data/quality_reports/{dataset_name}_stakeholder_report.md",
        "",
    ]

    return "\n".join(report_lines)


def onboard_dataset(dataset_name: str) -> None:
    """
    Run the full onboarding workflow for a registered dataset.
    """
    QUALITY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    dataset_config = get_dataset_config(dataset_name)
    df = read_dataset(dataset_config)

    column_profile = create_column_profile(df, dataset_name)

    if dataset_name == "counterparty_trade_links":
        rule_results, failed_records = validate_counterparty_trade_links(
            df,
            dataset_name,
            dataset_config,
        )
    else:
        raise NotImplementedError(
            f"No validation workflow has been implemented for {dataset_name}."
        )

    stakeholder_report = create_stakeholder_report(
        dataset_name,
        df,
        column_profile,
        rule_results,
        failed_records,
    )

    column_profile_path = QUALITY_REPORT_DIR / f"{dataset_name}_column_profile.csv"
    rule_results_path = QUALITY_REPORT_DIR / f"{dataset_name}_rule_results.csv"
    failed_records_path = QUALITY_REPORT_DIR / f"{dataset_name}_failed_records.csv"
    stakeholder_report_path = QUALITY_REPORT_DIR / f"{dataset_name}_stakeholder_report.md"

    column_profile.to_csv(column_profile_path, index=False)
    rule_results.to_csv(rule_results_path, index=False)
    failed_records.to_csv(failed_records_path, index=False)
    stakeholder_report_path.write_text(stakeholder_report, encoding="utf-8")

    print(f"New dataset onboarding completed for: {dataset_name}")
    print(f"Rows processed: {len(df):,}")
    print(f"Columns profiled: {len(df.columns):,}")
    print(f"Rules executed: {len(rule_results):,}")
    print(f"Rules with failures: {(rule_results['failed_count'] > 0).sum():,}")
    print(f"Failed record exceptions: {len(failed_records):,}")
    print("")
    print("Reports written to:")
    print(f"- {column_profile_path}")
    print(f"- {rule_results_path}")
    print(f"- {failed_records_path}")
    print(f"- {stakeholder_report_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Onboard a new dirty dataset into the EntityQ quality framework."
    )

    parser.add_argument(
        "--dataset",
        default="counterparty_trade_links",
        help="Registered dataset name to onboard.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    onboard_dataset(args.dataset)