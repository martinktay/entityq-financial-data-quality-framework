from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INCOMING_PATH = PROJECT_ROOT / "data" / "incoming" / "counterparty_trade_links.csv"
QUALITY_REPORT_DIR = PROJECT_ROOT / "data" / "quality_reports"
CURATED_DIR = PROJECT_ROOT / "data" / "curated"

CURATED_OUTPUT_PATH = CURATED_DIR / "counterparty_trade_links_curated.csv"
QUARANTINE_OUTPUT_PATH = CURATED_DIR / "counterparty_trade_links_quarantine.csv"
REMEDIATION_SUMMARY_PATH = QUALITY_REPORT_DIR / "counterparty_trade_links_remediation_summary.md"


VALID_CURRENCIES = {"USD", "GBP", "EUR", "NGN", "JPY", "CHF", "CAD", "AUD"}
VALID_COUNTRIES = {
    "US", "GB", "NG", "DE", "FR", "CA", "SG", "AE", "ZA", "NL",
    "CH", "IE", "IN", "BR", "AU", "JP", "HK", "LU"
}
VALID_INSTRUMENT_TYPES = {
    "Equity", "Bond", "Fund", "Private Credit", "Private Equity", "Derivative"
}
VALID_KYC_STATUSES = {"Approved", "Pending", "Rejected", "Expired"}
VALID_RISK_RATINGS = {"Low", "Medium", "High"}


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trim whitespace from object/string columns.
    """
    cleaned = df.copy()

    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        cleaned[column] = cleaned[column].fillna("").astype(str).str.strip()

    return cleaned


def standardise_common_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply safe standardisation rules.

    These are conservative fixes where the intended value is obvious.
    Ambiguous values are not forced; they remain quarantined for review.
    """
    cleaned = df.copy()

    currency_map = {
        "EURO": "EUR",
        "US": "USD",
        "U.S.D": "USD",
        "UKP": "GBP",
    }

    country_map = {
        "UK": "GB",
    }

    instrument_map = {
        "Equityy": "Equity",
    }

    cleaned["currency"] = cleaned["currency"].replace(currency_map)
    cleaned["risk_country"] = cleaned["risk_country"].replace(country_map)
    cleaned["booking_country"] = cleaned["booking_country"].replace(country_map)
    cleaned["instrument_type"] = cleaned["instrument_type"].replace(instrument_map)

    return cleaned


def add_remediation_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add remediation and quarantine flags.

    The framework does not pretend all issues can be fixed automatically.
    Some records are safe to standardise, while others must be quarantined
    for reference data, KYC, risk or operations review.
    """
    reviewed = df.copy()

    trade_id = reviewed["trade_id"].fillna("").astype(str).str.strip()
    counterparty_entity_id = reviewed["counterparty_entity_id"].fillna("").astype(str).str.strip()
    issuer_id = reviewed["issuer_id"].fillna("").astype(str).str.strip()
    counterparty_name = reviewed["counterparty_name"].fillna("").astype(str).str.strip()

    trade_date = pd.to_datetime(reviewed["trade_date"], errors="coerce")
    settlement_date = pd.to_datetime(reviewed["settlement_date"], errors="coerce")
    notional_amount = pd.to_numeric(reviewed["notional_amount"], errors="coerce")
    provider_confidence_score = pd.to_numeric(
        reviewed["provider_confidence_score"],
        errors="coerce",
    )

    duplicate_trade_id = trade_id.ne("") & trade_id.duplicated(keep=False)

    flags: list[list[str]] = []

    for index, row in reviewed.iterrows():
        row_flags: list[str] = []

        if trade_id.loc[index] == "":
            row_flags.append("missing_trade_id")

        if duplicate_trade_id.loc[index]:
            row_flags.append("duplicate_trade_id")

        if counterparty_entity_id.loc[index] == "":
            row_flags.append("missing_counterparty_entity_id")

        if counterparty_name.loc[index] in {"", "Unknown Counterparty"}:
            row_flags.append("weak_counterparty_name")

        if issuer_id.loc[index] == "" or issuer_id.loc[index].startswith("ISS-ORPHAN"):
            row_flags.append("invalid_or_orphan_issuer_id")

        if pd.isna(trade_date.loc[index]):
            row_flags.append("invalid_trade_date")

        if pd.isna(settlement_date.loc[index]):
            row_flags.append("invalid_settlement_date")

        if (
            pd.notna(trade_date.loc[index])
            and pd.notna(settlement_date.loc[index])
            and settlement_date.loc[index] < trade_date.loc[index]
        ):
            row_flags.append("settlement_before_trade_date")

        if pd.isna(notional_amount.loc[index]) or notional_amount.loc[index] <= 0:
            row_flags.append("invalid_notional_amount")

        if row["currency"] not in VALID_CURRENCIES:
            row_flags.append("invalid_currency")

        if row["risk_country"] not in VALID_COUNTRIES:
            row_flags.append("invalid_risk_country")

        if row["instrument_type"] not in VALID_INSTRUMENT_TYPES:
            row_flags.append("invalid_instrument_type")

        if row["kyc_status"] not in VALID_KYC_STATUSES:
            row_flags.append("invalid_kyc_status")

        if row["counterparty_risk_rating"] not in VALID_RISK_RATINGS:
            row_flags.append("invalid_counterparty_risk_rating")

        if (
            row["counterparty_risk_rating"] == "High"
            and row["kyc_status"] != "Approved"
        ):
            row_flags.append("high_risk_incomplete_kyc")

        if (
            pd.isna(provider_confidence_score.loc[index])
            or provider_confidence_score.loc[index] < 0
            or provider_confidence_score.loc[index] > 1
        ):
            row_flags.append("invalid_provider_confidence_score")
        elif provider_confidence_score.loc[index] < 0.70:
            row_flags.append("low_provider_confidence_score")

        flags.append(row_flags)

    reviewed["remediation_flags"] = [";".join(flag_list) for flag_list in flags]
    reviewed["issue_count"] = [len(flag_list) for flag_list in flags]

    return reviewed


def split_curated_and_quarantine(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split records into curated and quarantined outputs.

    Curated records have no blocking issues.
    Quarantined records need analyst/reference data/KYC review.
    """
    blocking_issue_keywords = [
        "missing_trade_id",
        "duplicate_trade_id",
        "missing_counterparty_entity_id",
        "invalid_or_orphan_issuer_id",
        "invalid_trade_date",
        "invalid_settlement_date",
        "settlement_before_trade_date",
        "invalid_notional_amount",
        "invalid_currency",
        "invalid_risk_country",
        "invalid_instrument_type",
        "invalid_kyc_status",
        "invalid_counterparty_risk_rating",
        "high_risk_incomplete_kyc",
        "invalid_provider_confidence_score",
    ]

    def has_blocking_issue(flag_text: str) -> bool:
        return any(keyword in flag_text for keyword in blocking_issue_keywords)

    quarantine_mask = df["remediation_flags"].apply(has_blocking_issue)

    quarantine = df[quarantine_mask].copy()
    curated = df[~quarantine_mask].copy()

    curated["curation_status"] = "accepted"
    quarantine["curation_status"] = "quarantined_for_review"

    curated["curated_at"] = datetime.now(timezone.utc).isoformat()
    quarantine["curated_at"] = datetime.now(timezone.utc).isoformat()

    return curated, quarantine


def create_remediation_summary(
    original: pd.DataFrame,
    reviewed: pd.DataFrame,
    curated: pd.DataFrame,
    quarantine: pd.DataFrame,
) -> str:
    """
    Create a markdown summary of remediation outcomes.
    """
    total_rows = len(original)
    issue_rows = int((reviewed["issue_count"] > 0).sum())

    top_flags = (
        reviewed["remediation_flags"]
        .str.split(";")
        .explode()
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .head(15)
    )

    top_flags_table = (
        top_flags
        .reset_index()
        .rename(columns={"index": "issue_type", "remediation_flags": "count"})
        .to_markdown(index=False)
        if not top_flags.empty
        else "No remediation flags found."
    )

    lines = [
        "# Counterparty Trade Links Remediation Summary",
        "",
        "## Executive Summary",
        "",
        f"- Total incoming records: {total_rows:,}",
        f"- Records with at least one issue: {issue_rows:,}",
        f"- Records accepted into curated output: {len(curated):,}",
        f"- Records quarantined for review: {len(quarantine):,}",
        f"- Curated acceptance rate: {round((len(curated) / total_rows) * 100, 2) if total_rows else 0}%",
        f"- Quarantine rate: {round((len(quarantine) / total_rows) * 100, 2) if total_rows else 0}%",
        "",
        "## Remediation Approach",
        "",
        "The remediation layer applies safe standardisation rules where the intended value is clear, such as mapping `EURO` to `EUR` and `UK` to `GB`.",
        "",
        "Records with blocking issues are not forced into the curated dataset. They are quarantined for analyst, reference data, KYC, risk, or operations review.",
        "",
        "## Top Remediation Flags",
        "",
        top_flags_table,
        "",
        "## Outputs",
        "",
        "- data/curated/counterparty_trade_links_curated.csv",
        "- data/curated/counterparty_trade_links_quarantine.csv",
        "- data/quality_reports/counterparty_trade_links_remediation_summary.md",
        "",
    ]

    return "\n".join(lines)


def run_remediation() -> None:
    """
    Run the remediation workflow for the counterparty trade-linked dataset.
    """
    if not INCOMING_PATH.exists():
        raise FileNotFoundError(
            f"Incoming dataset not found: {INCOMING_PATH}. "
            "Place counterparty_trade_links.csv in data/incoming."
        )

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    original = pd.read_csv(INCOMING_PATH)
    cleaned = clean_text_columns(original)
    cleaned = standardise_common_values(cleaned)
    reviewed = add_remediation_flags(cleaned)
    curated, quarantine = split_curated_and_quarantine(reviewed)

    curated.to_csv(CURATED_OUTPUT_PATH, index=False)
    quarantine.to_csv(QUARANTINE_OUTPUT_PATH, index=False)

    summary = create_remediation_summary(
        original=original,
        reviewed=reviewed,
        curated=curated,
        quarantine=quarantine,
    )

    REMEDIATION_SUMMARY_PATH.write_text(summary, encoding="utf-8")

    print("Counterparty trade remediation completed.")
    print(f"Incoming records: {len(original):,}")
    print(f"Curated records: {len(curated):,}")
    print(f"Quarantined records: {len(quarantine):,}")
    print("")
    print("Outputs written to:")
    print(f"- {CURATED_OUTPUT_PATH}")
    print(f"- {QUARANTINE_OUTPUT_PATH}")
    print(f"- {REMEDIATION_SUMMARY_PATH}")


if __name__ == "__main__":
    run_remediation()