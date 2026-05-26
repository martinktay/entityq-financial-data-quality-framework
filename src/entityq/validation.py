from __future__ import annotations

from pathlib import Path

import pandas as pd


VALID_COUNTRIES = {
    "US", "GB", "NG", "DE", "FR", "CA", "SG", "AE", "ZA", "NL",
    "CH", "IE", "IN", "BR", "AU", "JP", "HK", "LU"
}

VALID_ENTITY_TYPES = {
    "Public Company",
    "Private Company",
    "Fund",
    "SPV",
    "Government Entity",
    "Financial Institution",
}

VALID_STATUS = {"Active", "Inactive", "Merged", "Dissolved", "Unknown"}

VALID_INSTRUMENT_TYPES = {
    "Equity",
    "Bond",
    "Fund",
    "Commercial Paper",
    "Private Credit",
}

VALID_RISK_RATINGS = {"Low", "Medium", "High", "Critical"}


def _add_result(
    results: list[dict],
    table_name: str,
    rule_id: str,
    dimension: str,
    description: str,
    failed_mask: pd.Series,
    df: pd.DataFrame,
    severity: str,
    recommendation: str,
    example_columns: list[str],
) -> None:
    """
    Convert one validation check into a standard result row.

    failed_mask is a boolean Series:
    - True means the row failed the rule.
    - False means the row passed the rule.
    """
    failed_mask = failed_mask.fillna(False).astype(bool)

    total_count = len(df)
    failed_count = int(failed_mask.sum())
    passed_count = total_count - failed_count
    pass_rate = round(passed_count / total_count, 4) if total_count else 1.0

    columns = [column for column in example_columns if column in df.columns]
    failed_examples = df.loc[failed_mask, columns].head(5).to_dict(orient="records")

    results.append(
        {
            "table_name": table_name,
            "rule_id": rule_id,
            "dimension": dimension,
            "severity": severity,
            "description": description,
            "total_count": total_count,
            "failed_count": failed_count,
            "passed_count": passed_count,
            "pass_rate": pass_rate,
            "recommendation": recommendation,
            "failed_examples": str(failed_examples),
        }
    )


def validate_entities(entities: pd.DataFrame) -> list[dict]:
    """
    Validate the entity master table.

    This is the most important table because issuer, hierarchy, KYC and
    provider feed records depend on reliable entity records.
    """
    results: list[dict] = []
    today = pd.Timestamp.today().normalize()

    incorporation_date = pd.to_datetime(entities["incorporation_date"], errors="coerce")
    last_verified_date = pd.to_datetime(entities["last_verified_date"], errors="coerce")

    _add_result(
        results,
        "entities",
        "ENT-001",
        "Completeness",
        "entity_id must not be null.",
        entities["entity_id"].isna(),
        entities,
        "Critical",
        "Ensure every entity has a stable master identifier.",
        ["entity_id", "legal_name", "source_system"],
    )

    _add_result(
        results,
        "entities",
        "ENT-002",
        "Uniqueness",
        "entity_id must be unique.",
        entities["entity_id"].duplicated(keep=False),
        entities,
        "Critical",
        "Investigate duplicate entity IDs and apply survivorship rules.",
        ["entity_id", "legal_name", "country_code", "source_system"],
    )

    _add_result(
        results,
        "entities",
        "ENT-003",
        "Completeness",
        "legal_name must not be null.",
        entities["legal_name"].isna(),
        entities,
        "High",
        "Request missing legal names from the source owner or provider.",
        ["entity_id", "legal_name", "source_system"],
    )

    _add_result(
        results,
        "entities",
        "ENT-004",
        "Validity",
        "country_code must be in the approved country list.",
        ~entities["country_code"].isin(VALID_COUNTRIES),
        entities,
        "High",
        "Standardise invalid country codes.",
        ["entity_id", "legal_name", "country_code", "source_system"],
    )

    _add_result(
        results,
        "entities",
        "ENT-005",
        "Validity",
        "entity_type must be in the approved taxonomy.",
        ~entities["entity_type"].isin(VALID_ENTITY_TYPES),
        entities,
        "Medium",
        "Map unsupported entity types to the approved taxonomy.",
        ["entity_id", "legal_name", "entity_type"],
    )

    _add_result(
        results,
        "entities",
        "ENT-006",
        "Validity",
        "status must be in the approved status list.",
        ~entities["status"].isin(VALID_STATUS),
        entities,
        "Medium",
        "Standardise status values across source systems.",
        ["entity_id", "legal_name", "status"],
    )

    _add_result(
        results,
        "entities",
        "ENT-007",
        "Validity",
        "incorporation_date cannot be in the future.",
        incorporation_date > today,
        entities,
        "High",
        "Review future incorporation dates with the source owner.",
        ["entity_id", "legal_name", "incorporation_date"],
    )

    _add_result(
        results,
        "entities",
        "ENT-008",
        "Timeliness",
        "active entity records should be verified within the last 365 days.",
        (entities["status"] == "Active") & ((today - last_verified_date).dt.days > 365),
        entities,
        "Medium",
        "Prioritise stale active entities for review.",
        ["entity_id", "legal_name", "status", "last_verified_date"],
    )

    _add_result(
        results,
        "entities",
        "ENT-009",
        "Completeness",
        "private companies should have a registration number where available.",
        (entities["entity_type"] == "Private Company") & entities["registration_number"].isna(),
        entities,
        "Medium",
        "Improve enrichment for private company registration numbers.",
        ["entity_id", "legal_name", "entity_type", "registration_number"],
    )

    return results


def validate_issuers(issuers: pd.DataFrame, entities: pd.DataFrame) -> list[dict]:
    """
    Validate issuer records.

    Issuers should link to valid master entity records.
    """
    results: list[dict] = []
    valid_entity_ids = set(entities["entity_id"].dropna())

    _add_result(
        results,
        "issuers",
        "ISS-001",
        "Completeness",
        "issuer_id must not be null.",
        issuers["issuer_id"].isna(),
        issuers,
        "Critical",
        "Ensure every issuer record has a stable issuer identifier.",
        ["issuer_id", "entity_id", "issuer_name"],
    )

    _add_result(
        results,
        "issuers",
        "ISS-002",
        "Uniqueness",
        "issuer_id must be unique.",
        issuers["issuer_id"].duplicated(keep=False),
        issuers,
        "Critical",
        "Investigate duplicate issuer records.",
        ["issuer_id", "entity_id", "issuer_name"],
    )

    _add_result(
        results,
        "issuers",
        "ISS-003",
        "Referential Integrity",
        "issuer entity_id must exist in the entity master table.",
        ~issuers["entity_id"].isin(valid_entity_ids),
        issuers,
        "Critical",
        "Fix orphan issuer records by matching them to valid entity IDs.",
        ["issuer_id", "entity_id", "issuer_name", "source_system"],
    )

    _add_result(
        results,
        "issuers",
        "ISS-004",
        "Validity",
        "instrument_type must be in the approved instrument list.",
        ~issuers["instrument_type"].isin(VALID_INSTRUMENT_TYPES),
        issuers,
        "Medium",
        "Map invalid instrument types to the approved taxonomy.",
        ["issuer_id", "entity_id", "instrument_type"],
    )

    _add_result(
        results,
        "issuers",
        "ISS-005",
        "Completeness",
        "listed issuers should have an exchange code.",
        (issuers["listing_status"] == "Listed") & issuers["exchange_code"].isna(),
        issuers,
        "High",
        "Request missing exchange codes for listed issuers.",
        ["issuer_id", "entity_id", "listing_status", "exchange_code"],
    )

    return results


def validate_hierarchy(hierarchy: pd.DataFrame, entities: pd.DataFrame) -> list[dict]:
    """
    Validate corporate hierarchy records.

    This checks parent-child relationship quality.
    """
    results: list[dict] = []
    valid_entity_ids = set(entities["entity_id"].dropna())

    pairs = set(zip(hierarchy["child_entity_id"], hierarchy["parent_entity_id"]))

    circular_mask = hierarchy.apply(
        lambda row: (row["parent_entity_id"], row["child_entity_id"]) in pairs,
        axis=1,
    )

    _add_result(
        results,
        "entity_hierarchy",
        "HIER-001",
        "Referential Integrity",
        "child_entity_id must exist in entity master.",
        ~hierarchy["child_entity_id"].isin(valid_entity_ids),
        hierarchy,
        "Critical",
        "Resolve orphan child entities before publishing hierarchy data.",
        ["child_entity_id", "parent_entity_id", "source_system"],
    )

    _add_result(
        results,
        "entity_hierarchy",
        "HIER-002",
        "Referential Integrity",
        "parent_entity_id must exist in entity master.",
        ~hierarchy["parent_entity_id"].isin(valid_entity_ids),
        hierarchy,
        "Critical",
        "Resolve orphan parent entities before publishing hierarchy data.",
        ["child_entity_id", "parent_entity_id", "source_system"],
    )

    _add_result(
        results,
        "entity_hierarchy",
        "HIER-003",
        "Validity",
        "child_entity_id cannot equal parent_entity_id.",
        hierarchy["child_entity_id"] == hierarchy["parent_entity_id"],
        hierarchy,
        "High",
        "Remove self-referencing hierarchy relationships.",
        ["child_entity_id", "parent_entity_id", "relationship_type"],
    )

    _add_result(
        results,
        "entity_hierarchy",
        "HIER-004",
        "Validity",
        "ownership_percentage must be between 0 and 100.",
        ~hierarchy["ownership_percentage"].between(0, 100),
        hierarchy,
        "High",
        "Review ownership percentages outside the valid range.",
        ["child_entity_id", "parent_entity_id", "ownership_percentage"],
    )

    _add_result(
        results,
        "entity_hierarchy",
        "HIER-005",
        "Hierarchy Integrity",
        "hierarchy should not contain circular parent-child relationships.",
        circular_mask,
        hierarchy,
        "High",
        "Investigate circular relationships and apply hierarchy survivorship rules.",
        ["child_entity_id", "parent_entity_id", "relationship_type"],
    )

    return results


def validate_kyc(kyc: pd.DataFrame, entities: pd.DataFrame) -> list[dict]:
    """
    Validate KYC and counterparty risk data.

    High-risk entities must have reliable and timely reviews.
    """
    results: list[dict] = []
    today = pd.Timestamp.today().normalize()

    valid_entity_ids = set(entities["entity_id"].dropna())
    last_review_date = pd.to_datetime(kyc["last_review_date"], errors="coerce")
    next_review_due_date = pd.to_datetime(kyc["next_review_due_date"], errors="coerce")

    _add_result(
        results,
        "kyc_attributes",
        "KYC-001",
        "Referential Integrity",
        "KYC entity_id must exist in entity master.",
        ~kyc["entity_id"].isin(valid_entity_ids),
        kyc,
        "Critical",
        "Resolve orphan KYC records or create missing master entity records.",
        ["entity_id", "kyc_status", "risk_rating", "source_system"],
    )

    _add_result(
        results,
        "kyc_attributes",
        "KYC-002",
        "Validity",
        "risk_rating must be Low, Medium, High, or Critical.",
        ~kyc["risk_rating"].isin(VALID_RISK_RATINGS),
        kyc,
        "High",
        "Map invalid risk ratings to the approved risk taxonomy.",
        ["entity_id", "risk_rating", "source_system"],
    )

    _add_result(
        results,
        "kyc_attributes",
        "KYC-003",
        "Timeliness",
        "High and Critical risk counterparties should have been reviewed within 365 days.",
        kyc["risk_rating"].isin(["High", "Critical"]) & ((today - last_review_date).dt.days > 365),
        kyc,
        "Critical",
        "Prioritise stale high-risk counterparties for review.",
        ["entity_id", "risk_rating", "last_review_date"],
    )

    _add_result(
        results,
        "kyc_attributes",
        "KYC-004",
        "Timeliness",
        "next_review_due_date should not be overdue.",
        next_review_due_date < today,
        kyc,
        "High",
        "Trigger remediation workflow for overdue KYC reviews.",
        ["entity_id", "risk_rating", "next_review_due_date"],
    )

    return results


def validate_provider_feed(provider: pd.DataFrame, entities: pd.DataFrame) -> list[dict]:
    """
    Validate third-party provider feed data.
    """
    results: list[dict] = []
    known_registration_numbers = set(entities["registration_number"].dropna())

    _add_result(
        results,
        "provider_feed",
        "PRV-001",
        "Uniqueness",
        "provider_record_id must be unique.",
        provider["provider_record_id"].duplicated(keep=False),
        provider,
        "High",
        "Investigate duplicated records from third-party provider feeds.",
        ["provider_record_id", "provider_name", "legal_name"],
    )

    _add_result(
        results,
        "provider_feed",
        "PRV-002",
        "Completeness",
        "provider legal_name must not be null.",
        provider["legal_name"].isna(),
        provider,
        "High",
        "Reject provider records without legal names or return them for enrichment.",
        ["provider_record_id", "provider_name", "legal_name"],
    )

    _add_result(
        results,
        "provider_feed",
        "PRV-003",
        "Validity",
        "confidence_score must be between 0 and 1.",
        ~provider["confidence_score"].between(0, 1),
        provider,
        "Medium",
        "Standardise provider confidence scores and reject invalid values.",
        ["provider_record_id", "provider_name", "confidence_score"],
    )

    _add_result(
        results,
        "provider_feed",
        "PRV-004",
        "Consistency",
        "provider registration_number should match an internal master record where available.",
        provider["registration_number"].notna()
        & ~provider["registration_number"].isin(known_registration_numbers),
        provider,
        "Medium",
        "Run entity matching and investigate unmatched provider records.",
        ["provider_record_id", "legal_name", "registration_number"],
    )

    return results


def run_validation(
    input_dir: str | Path = "data/raw",
    output_dir: str | Path = "data/quality_reports",
) -> pd.DataFrame:
    """
    Run all validation checks and export a rule-level results file.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entities = pd.read_csv(input_dir / "entities.csv")
    issuers = pd.read_csv(input_dir / "issuers.csv")
    hierarchy = pd.read_csv(input_dir / "entity_hierarchy.csv")
    kyc = pd.read_csv(input_dir / "kyc_attributes.csv")
    provider = pd.read_csv(input_dir / "provider_feed.csv")

    results: list[dict] = []
    results.extend(validate_entities(entities))
    results.extend(validate_issuers(issuers, entities))
    results.extend(validate_hierarchy(hierarchy, entities))
    results.extend(validate_kyc(kyc, entities))
    results.extend(validate_provider_feed(provider, entities))

    results_df = pd.DataFrame(results)
    results_df.to_csv(output_dir / "rule_results.csv", index=False)

    return results_df


if __name__ == "__main__":
    validation_results = run_validation()
    print("Validation completed.")
    print("Output written to: data/quality_reports/rule_results.csv")
    print(validation_results[["table_name", "rule_id", "dimension", "failed_count", "pass_rate"]])