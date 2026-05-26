from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd


VALID_COUNTRIES = [
    "US", "GB", "NG", "DE", "FR", "CA", "SG", "AE", "ZA", "NL",
    "CH", "IE", "IN", "BR", "AU", "JP", "HK", "LU"
]

INVALID_COUNTRIES = ["XX", "ZZZ", "N/A", "", None]

ENTITY_TYPES = [
    "Public Company",
    "Private Company",
    "Fund",
    "SPV",
    "Government Entity",
    "Financial Institution",
]

BAD_ENTITY_TYPES = ["UnknownType", "Private", "Company?", "", None]

SECTORS = [
    "Financials", "Energy", "Technology", "Healthcare", "Industrials",
    "Consumer Goods", "Telecommunications", "Utilities", "Real Estate",
    "Materials",
]

INDUSTRIES = [
    "Banking", "Oil & Gas", "Software", "Pharmaceuticals", "Logistics",
    "Retail", "Telecom Services", "Power Generation", "Private Equity",
    "Mining",
]

STATUSES = ["Active", "Inactive", "Merged", "Dissolved", "Unknown"]
BAD_STATUSES = ["Running", "Closed?", "", None]

SOURCE_SYSTEMS = [
    "Internal Master",
    "ProviderA",
    "ProviderB",
    "KYC Platform",
    "Issuer Feed",
    "Manual Upload",
]

COMPANY_STEMS = [
    "Northbridge", "Korefield", "Atlas", "Riverstone", "BluePeak",
    "Sterling", "Nova", "Cedar", "Helios", "Summit", "Crestline",
    "Lagos Continental", "Albion", "Meridian", "Oakwell", "Falcon",
    "Horizon", "Greenfield", "Redwood", "Frontier", "PrimeEdge",
    "Silvergate", "Westbridge", "Granite", "Union",
]

COMPANY_SUFFIXES = [
    "Limited", "Ltd", "PLC", "Holdings", "Group", "Capital",
    "Energy", "Technologies", "Partners", "Industries", "Investments",
    "Corporation", "Services", "Finance",
]


def _random_dates(
    rng: np.random.Generator,
    count: int,
    start: str,
    end: str,
) -> pd.Series:
    """
    Generate random dates between two dates.

    This is used for incorporation dates, verification dates, KYC review dates,
    and provider feed dates.
    """
    start_ts = pd.Timestamp(start).value // 10**9
    end_ts = pd.Timestamp(end).value // 10**9
    values = rng.integers(start_ts, end_ts, size=count)
    return pd.Series(pd.to_datetime(values, unit="s").strftime("%Y-%m-%d"))


def _normalise_name(name: object) -> object:
    """
    Create a simplified version of a legal entity name.

    Example:
    'Northbridge Holdings Limited' becomes 'NORTHBRIDGE'.

    This helps with entity matching, duplicate detection, and provider feed comparison.
    """
    if pd.isna(name):
        return None

    text = str(name).upper()
    text = re.sub(r"[^A-Z0-9 ]", " ", text)

    words_to_remove = [
        "LIMITED", "LTD", "PLC", "INC", "CORP", "CORPORATION",
        "LLC", "HOLDINGS", "GROUP",
    ]

    for word in words_to_remove:
        text = re.sub(rf"\b{word}\b", " ", text)

    return " ".join(text.split())


def _company_name(rng: np.random.Generator) -> str:
    """
    Generate a synthetic but realistic company name.
    """
    return f"{rng.choice(COMPANY_STEMS)} {rng.choice(COMPANY_SUFFIXES)}"


def generate_entities(
    output_dir: str | Path,
    entity_count: int = 5000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate the main entity master table.

    This table represents financial entity/reference data. Other tables such as
    issuers, hierarchy, KYC, and provider feeds link back to it.
    """
    rng = np.random.default_rng(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entity_ids = [f"ENT{str(i).zfill(6)}" for i in range(1, entity_count + 1)]
    legal_names = [_company_name(rng) for _ in range(entity_count)]
    countries = rng.choice(VALID_COUNTRIES, size=entity_count)

    entity_types = rng.choice(
        ENTITY_TYPES,
        size=entity_count,
        p=[0.16, 0.43, 0.11, 0.08, 0.06, 0.16],
    )

    statuses = rng.choice(
        STATUSES,
        size=entity_count,
        p=[0.72, 0.09, 0.05, 0.05, 0.09],
    )

    registration_numbers = [
        f"{country}-{rng.integers(100000, 999999)}" for country in countries
    ]

    entities = pd.DataFrame(
        {
            "entity_id": entity_ids,
            "legal_name": legal_names,
            "normalized_name": [_normalise_name(name) for name in legal_names],
            "country_code": countries,
            "registration_number": registration_numbers,
            "entity_type": entity_types,
            "sector": rng.choice(SECTORS, size=entity_count),
            "industry": rng.choice(INDUSTRIES, size=entity_count),
            "status": statuses,
            "incorporation_date": _random_dates(rng, entity_count, "1980-01-01", "2023-12-31"),
            "last_verified_date": _random_dates(rng, entity_count, "2021-01-01", "2025-01-01"),
            "source_system": rng.choice(SOURCE_SYSTEMS, size=entity_count),
            "created_at": _random_dates(rng, entity_count, "2020-01-01", "2024-06-30"),
            "updated_at": _random_dates(rng, entity_count, "2023-01-01", "2025-02-28"),
        }
    )

    # Issue 1: Missing legal names.
    missing_name_idx = rng.choice(
        entities.index,
        size=int(entity_count * 0.015),
        replace=False,
    )
    entities.loc[missing_name_idx, "legal_name"] = None
    entities.loc[missing_name_idx, "normalized_name"] = None

    # Issue 2: Missing registration numbers.
    missing_reg_idx = rng.choice(
        entities.index,
        size=int(entity_count * 0.05),
        replace=False,
    )
    entities.loc[missing_reg_idx, "registration_number"] = None

    # Issue 3: Invalid country codes.
    invalid_country_idx = rng.choice(
        entities.index,
        size=int(entity_count * 0.025),
        replace=False,
    )
    entities.loc[invalid_country_idx, "country_code"] = rng.choice(
        INVALID_COUNTRIES,
        size=len(invalid_country_idx),
    )

    # Issue 4: Invalid entity types.
    invalid_type_idx = rng.choice(
        entities.index,
        size=int(entity_count * 0.015),
        replace=False,
    )
    entities.loc[invalid_type_idx, "entity_type"] = rng.choice(
        BAD_ENTITY_TYPES,
        size=len(invalid_type_idx),
    )

    # Issue 5: Invalid statuses.
    invalid_status_idx = rng.choice(
        entities.index,
        size=int(entity_count * 0.01),
        replace=False,
    )
    entities.loc[invalid_status_idx, "status"] = rng.choice(
        BAD_STATUSES,
        size=len(invalid_status_idx),
    )

    # Issue 6: Future incorporation dates.
    future_inc_idx = rng.choice(
        entities.index,
        size=int(entity_count * 0.01),
        replace=False,
    )
    entities.loc[future_inc_idx, "incorporation_date"] = _random_dates(
        rng,
        len(future_inc_idx),
        "2027-01-01",
        "2030-12-31",
    ).values

    # Issue 7: Stale verification dates.
    stale_idx = rng.choice(
        entities.index,
        size=int(entity_count * 0.06),
        replace=False,
    )
    entities.loc[stale_idx, "last_verified_date"] = _random_dates(
        rng,
        len(stale_idx),
        "2015-01-01",
        "2020-12-31",
    ).values

    # Issue 8: Duplicate entity IDs.
    duplicate_count = int(entity_count * 0.02)
    duplicate_rows = entities.sample(duplicate_count, random_state=seed).copy()
    duplicate_rows["source_system"] = "ProviderB"

    entities = pd.concat([entities, duplicate_rows], ignore_index=True)

    entities.to_csv(output_dir / "entities.csv", index=False)
    return entities


def generate_issuers(
    entities: pd.DataFrame,
    output_dir: str | Path,
    issuer_count: int = 1500,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate issuer records linked to entity records.

    Some issuer records deliberately point to invalid entity IDs so we can test
    referential integrity.
    """
    rng = np.random.default_rng(seed + 1)
    output_dir = Path(output_dir)

    valid_entity_ids = entities["entity_id"].dropna().unique()
    orphan_ids = np.array([f"ENT_ORPHAN_{i}" for i in range(1, 76)])
    entity_choices = np.concatenate([valid_entity_ids, orphan_ids])

    issuers = pd.DataFrame(
        {
            "issuer_id": [f"ISS{str(i).zfill(6)}" for i in range(1, issuer_count + 1)],
            "entity_id": rng.choice(entity_choices, size=issuer_count),
            "issuer_name": [_company_name(rng) for _ in range(issuer_count)],
            "instrument_type": rng.choice(
                [
                    "Equity",
                    "Bond",
                    "Fund",
                    "Commercial Paper",
                    "Private Credit",
                    "InvalidInstrument",
                ],
                size=issuer_count,
                p=[0.30, 0.27, 0.16, 0.10, 0.13, 0.04],
            ),
            "market": rng.choice(["Public", "Private", "OTC"], size=issuer_count),
            "listing_status": rng.choice(["Listed", "Unlisted", "Delisted"], size=issuer_count),
            "exchange_code": rng.choice(
                ["NYSE", "LSE", "NGX", "NASDAQ", "XETRA", None],
                size=issuer_count,
            ),
            "risk_country": rng.choice(VALID_COUNTRIES + INVALID_COUNTRIES, size=issuer_count),
            "source_system": rng.choice(
                ["Issuer Feed", "ProviderA", "ProviderB", "Manual Upload"],
                size=issuer_count,
            ),
        }
    )

    # Issue: Some listed issuers have no exchange code.
    listed_idx = issuers[issuers["listing_status"] == "Listed"].sample(
        frac=0.08,
        random_state=seed,
    ).index
    issuers.loc[listed_idx, "exchange_code"] = None

    # Issue: Duplicate issuer IDs.
    duplicate_rows = issuers.sample(int(issuer_count * 0.01), random_state=seed).copy()
    issuers = pd.concat([issuers, duplicate_rows], ignore_index=True)

    issuers.to_csv(output_dir / "issuers.csv", index=False)
    return issuers


def generate_hierarchy(
    entities: pd.DataFrame,
    output_dir: str | Path,
    relationship_count: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate corporate hierarchy records.

    This simulates parent-child ownership relationships between legal entities.
    """
    rng = np.random.default_rng(seed + 2)
    output_dir = Path(output_dir)

    valid_entity_ids = entities["entity_id"].dropna().unique()
    orphan_ids = np.array([f"ENT_UNKNOWN_{i}" for i in range(1, 51)])
    entity_choices = np.concatenate([valid_entity_ids, orphan_ids])

    hierarchy = pd.DataFrame(
        {
            "child_entity_id": rng.choice(entity_choices, size=relationship_count),
            "parent_entity_id": rng.choice(entity_choices, size=relationship_count),
            "relationship_type": rng.choice(
                ["Parent", "Subsidiary", "Ultimate Parent", "Affiliate", "Unknown"],
                size=relationship_count,
            ),
            "ownership_percentage": rng.normal(loc=62, scale=28, size=relationship_count).round(2),
            "effective_from": _random_dates(rng, relationship_count, "2010-01-01", "2024-01-01"),
            "effective_to": rng.choice(
                list(_random_dates(rng, relationship_count, "2024-02-01", "2028-12-31")) + [None],
                size=relationship_count,
            ),
            "source_system": rng.choice(
                ["Internal Master", "ProviderA", "ProviderB"],
                size=relationship_count,
            ),
        }
    )

    # Issue: Some records say the child is its own parent.
    self_parent_idx = rng.choice(
        hierarchy.index,
        size=int(relationship_count * 0.01),
        replace=False,
    )
    hierarchy.loc[self_parent_idx, "parent_entity_id"] = hierarchy.loc[
        self_parent_idx,
        "child_entity_id",
    ]

    # Issue: Ownership percentage outside the valid 0-100 range.
    invalid_ownership_idx = rng.choice(
        hierarchy.index,
        size=int(relationship_count * 0.03),
        replace=False,
    )
    hierarchy.loc[invalid_ownership_idx, "ownership_percentage"] = rng.choice(
        [-25.0, 125.0, 150.0, np.nan],
        size=len(invalid_ownership_idx),
    )

    # Issue: Circular parent-child relationships.
    circular_sample = hierarchy.sample(20, random_state=seed).copy()
    circular_sample[["child_entity_id", "parent_entity_id"]] = circular_sample[
        ["parent_entity_id", "child_entity_id"]
    ].values

    hierarchy = pd.concat([hierarchy, circular_sample], ignore_index=True)

    hierarchy.to_csv(output_dir / "entity_hierarchy.csv", index=False)
    return hierarchy


def generate_kyc_attributes(
    entities: pd.DataFrame,
    output_dir: str | Path,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate KYC and counterparty risk records.
    """
    rng = np.random.default_rng(seed + 3)
    output_dir = Path(output_dir)

    valid_entity_ids = entities["entity_id"].dropna().unique()
    orphan_ids = np.array([f"ENT_KYC_ORPHAN_{i}" for i in range(1, 76)])

    record_count = int(len(valid_entity_ids) * 0.85)
    entity_choices = np.concatenate([valid_entity_ids, orphan_ids])

    kyc = pd.DataFrame(
        {
            "entity_id": rng.choice(entity_choices, size=record_count, replace=False),
            "kyc_status": rng.choice(
                ["Approved", "Pending", "Rejected", "Expired", "Unknown"],
                size=record_count,
            ),
            "risk_rating": rng.choice(
                ["Low", "Medium", "High", "Critical", "InvalidRisk"],
                size=record_count,
                p=[0.35, 0.32, 0.20, 0.08, 0.05],
            ),
            "sanctions_flag": rng.choice([True, False, "Y", "N", None], size=record_count),
            "pep_flag": rng.choice([True, False, "Y", "N", None], size=record_count),
            "counterparty_type": rng.choice(
                ["Client", "Supplier", "Issuer", "Fund", "Broker", "Unknown"],
                size=record_count,
            ),
            "last_review_date": _random_dates(rng, record_count, "2020-01-01", "2025-01-01"),
            "next_review_due_date": _random_dates(rng, record_count, "2024-01-01", "2027-12-31"),
            "source_system": rng.choice(
                ["KYC Platform", "Manual Upload", "ProviderA"],
                size=record_count,
            ),
        }
    )

    # Issue: Stale reviews for high-risk records.
    high_risk_idx = kyc[kyc["risk_rating"].isin(["High", "Critical"])].sample(
        frac=0.20,
        random_state=seed,
    ).index
    kyc.loc[high_risk_idx, "last_review_date"] = _random_dates(
        rng,
        len(high_risk_idx),
        "2017-01-01",
        "2021-01-01",
    ).values

    # Issue: Overdue next review dates.
    overdue_idx = rng.choice(
        kyc.index,
        size=int(record_count * 0.08),
        replace=False,
    )
    kyc.loc[overdue_idx, "next_review_due_date"] = _random_dates(
        rng,
        len(overdue_idx),
        "2020-01-01",
        "2023-12-31",
    ).values

    kyc.to_csv(output_dir / "kyc_attributes.csv", index=False)
    return kyc


def generate_provider_feed(
    entities: pd.DataFrame,
    output_dir: str | Path,
    provider_count: int = 3800,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate third-party provider feed data.

    This simulates an external reference data vendor feed with inconsistent names,
    duplicate records, missing values, and invalid confidence scores.
    """
    rng = np.random.default_rng(seed + 4)
    output_dir = Path(output_dir)

    sample = entities.sample(provider_count, replace=True, random_state=seed).reset_index(drop=True)

    provider_names = []
    for name in sample["legal_name"].fillna("Unknown Entity"):
        text = str(name)
        text = text.replace("Limited", "Ltd")
        text = text.replace("Corporation", "Corp")

        if rng.random() < 0.08:
            text = text.upper()

        if rng.random() < 0.04:
            text = text + " "

        provider_names.append(text)

    provider_feed = pd.DataFrame(
        {
            "provider_record_id": [f"PRV{str(i).zfill(7)}" for i in range(1, provider_count + 1)],
            "provider_name": rng.choice(["ProviderA", "ProviderB", "ProviderC"], size=provider_count),
            "legal_name": provider_names,
            "country_code": sample["country_code"].values,
            "registration_number": sample["registration_number"].values,
            "sector": sample["sector"].values,
            "status": sample["status"].values,
            "confidence_score": rng.normal(loc=0.82, scale=0.15, size=provider_count).round(3),
            "feed_date": _random_dates(rng, provider_count, "2024-01-01", "2025-03-31"),
        }
    )

    # Issue: Invalid confidence scores.
    bad_confidence_idx = rng.choice(
        provider_feed.index,
        size=int(provider_count * 0.03),
        replace=False,
    )
    provider_feed.loc[bad_confidence_idx, "confidence_score"] = rng.choice(
        [-0.30, 1.20, 1.50, np.nan],
        size=len(bad_confidence_idx),
    )

    # Issue: Missing provider legal names.
    missing_name_idx = rng.choice(
        provider_feed.index,
        size=int(provider_count * 0.02),
        replace=False,
    )
    provider_feed.loc[missing_name_idx, "legal_name"] = None

    # Issue: Duplicate provider record IDs.
    duplicate_rows = provider_feed.sample(int(provider_count * 0.015), random_state=seed).copy()
    provider_feed = pd.concat([provider_feed, duplicate_rows], ignore_index=True)

    provider_feed.to_csv(output_dir / "provider_feed.csv", index=False)
    return provider_feed


def generate_all(
    output_dir: str | Path = "data/raw",
    entity_count: int = 5000,
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """
    Generate all raw datasets for the project.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entities = generate_entities(output_dir, entity_count=entity_count, seed=seed)
    issuers = generate_issuers(entities, output_dir, seed=seed)
    hierarchy = generate_hierarchy(entities, output_dir, seed=seed)
    kyc = generate_kyc_attributes(entities, output_dir, seed=seed)
    provider_feed = generate_provider_feed(entities, output_dir, seed=seed)

    return {
        "entities": entities,
        "issuers": issuers,
        "entity_hierarchy": hierarchy,
        "kyc_attributes": kyc,
        "provider_feed": provider_feed,
    }


if __name__ == "__main__":
    generate_all()
    print("Synthetic messy financial entity datasets generated in data/raw")
