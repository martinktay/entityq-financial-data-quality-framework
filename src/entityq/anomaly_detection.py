from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def build_one_hot_encoder() -> OneHotEncoder:
    """
    Create a OneHotEncoder that works across different scikit-learn versions.

    Newer versions use sparse_output=False.
    Older versions use sparse=False.

    This small helper makes the project more robust.
    """
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def prepare_entity_features(entities: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw entity records into features suitable for anomaly detection.

    We do not use every column directly. Instead, we create features that describe
    the quality and behaviour of each record.

    Examples:
    - length of legal name
    - whether a registration number exists
    - how many days since the record was verified
    - how many important fields are missing
    - country code
    - entity type
    - status
    - source system
    """
    today = pd.Timestamp.today().normalize()
    last_verified_date = pd.to_datetime(
        entities["last_verified_date"],
        errors="coerce",
    )

    key_fields = [
        "legal_name",
        "country_code",
        "registration_number",
        "entity_type",
        "sector",
        "status",
        "last_verified_date",
    ]

    features = pd.DataFrame(
        {
            "legal_name_length": entities["legal_name"].fillna("").astype(str).str.len(),
            "has_registration_number": entities["registration_number"].notna().astype(int),
            "days_since_verified": (today - last_verified_date).dt.days,
            "missing_field_count": entities[key_fields].isna().sum(axis=1),
            "country_code": entities["country_code"].fillna("MISSING"),
            "entity_type": entities["entity_type"].fillna("MISSING"),
            "status": entities["status"].fillna("MISSING"),
            "source_system": entities["source_system"].fillna("MISSING"),
        }
    )

    return features


def run_anomaly_detection(
    input_dir: str | Path = "data/raw",
    output_dir: str | Path = "data/quality_reports",
) -> pd.DataFrame:
    """
    Run anomaly detection on entity master records.

    The model used is Isolation Forest. It is useful for finding records that
    behave differently from the majority of the dataset.

    Output:
    - data/quality_reports/entity_anomalies.csv
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entities_path = input_dir / "entities.csv"

    if not entities_path.exists():
        raise FileNotFoundError(
            "entities.csv was not found. Run data_generation.py first."
        )

    entities = pd.read_csv(entities_path)
    features = prepare_entity_features(entities)

    numeric_features = [
        "legal_name_length",
        "has_registration_number",
        "days_since_verified",
        "missing_field_count",
    ]

    categorical_features = [
        "country_code",
        "entity_type",
        "status",
        "source_system",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                SimpleImputer(strategy="median"),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", build_one_hot_encoder()),
                    ]
                ),
                categorical_features,
            ),
        ]
    )

    model = IsolationForest(
        n_estimators=150,
        contamination=0.03,
        random_state=42,
    )

    transformed_features = preprocessor.fit_transform(features)

    anomaly_labels = model.fit_predict(transformed_features)
    anomaly_scores = model.decision_function(transformed_features)

    output = entities.copy()
    output["anomaly_label"] = np.where(anomaly_labels == -1, "Anomaly", "Normal")
    output["anomaly_score"] = anomaly_scores.round(5)

    anomalies = (
        output[output["anomaly_label"] == "Anomaly"]
        .sort_values("anomaly_score", ascending=True)
        .head(200)
    )

    anomalies.to_csv(output_dir / "entity_anomalies.csv", index=False)

    return anomalies


if __name__ == "__main__":
    anomaly_results = run_anomaly_detection()

    print("Anomaly detection completed.")
    print("Output written to: data/quality_reports/entity_anomalies.csv")
    print("")
    print("Top anomaly candidates:")
    print(
        anomaly_results[
            [
                "entity_id",
                "legal_name",
                "country_code",
                "entity_type",
                "status",
                "source_system",
                "anomaly_score",
            ]
        ].head(20)
    )