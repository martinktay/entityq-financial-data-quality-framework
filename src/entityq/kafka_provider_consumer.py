from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from confluent_kafka import Consumer, KafkaException


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STREAMING_DIR = PROJECT_ROOT / "data" / "streaming"
QUALITY_REPORT_DIR = PROJECT_ROOT / "data" / "quality_reports"

DEFAULT_TOPIC = "provider-feed-raw"
DEFAULT_BOOTSTRAP_SERVER = "localhost:9092"

VALID_COUNTRIES = {
    "US", "GB", "NG", "DE", "FR", "CA", "SG", "AE", "ZA", "NL",
    "CH", "IE", "IN", "BR", "AU", "JP", "HK", "LU"
}


def load_latest_run_metadata() -> dict[str, Any]:
    """
    Load the metadata written by the Kafka producer.

    The metadata tells this consumer which run_id to read and how many events
    were published in the latest run.
    """
    metadata_path = STREAMING_DIR / "kafka_run_metadata.json"

    if not metadata_path.exists():
        raise FileNotFoundError(
            "kafka_run_metadata.json was not found. "
            "Run kafka_provider_producer.py first."
        )

    return json.loads(metadata_path.read_text(encoding="utf-8"))


def validate_provider_payload(payload: dict[str, Any]) -> list[str]:
    """
    Validate one provider feed payload from Kafka.

    These checks simulate event-level validation before provider records are
    accepted into a curated reference data layer.
    """
    issues: list[str] = []

    legal_name = payload.get("legal_name")
    country_code = payload.get("country_code")
    confidence_score = payload.get("confidence_score")

    if legal_name is None or str(legal_name).strip() == "":
        issues.append("Missing legal name")

    if country_code not in VALID_COUNTRIES:
        issues.append("Invalid country code")

    try:
        score = float(confidence_score)

        if score < 0 or score > 1:
            issues.append("Invalid confidence score")

    except (TypeError, ValueError):
        issues.append("Invalid confidence score")

    return issues


def event_to_validation_result(event: dict[str, Any]) -> dict[str, Any]:
    """
    Convert one Kafka event into a validation result row.
    """
    payload = event["payload"]
    issues = validate_provider_payload(payload)

    return {
        "event_id": event["event_id"],
        "run_id": event["run_id"],
        "event_type": event["event_type"],
        "event_time": event["event_time"],
        "sequence_number": event["sequence_number"],
        "provider_record_id": payload.get("provider_record_id"),
        "provider_name": payload.get("provider_name"),
        "legal_name": payload.get("legal_name"),
        "country_code": payload.get("country_code"),
        "confidence_score": payload.get("confidence_score"),
        "status": "failed" if issues else "passed",
        "issue_count": len(issues),
        "issues": "; ".join(issues),
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }


def consume_provider_feed_events(
    topic: str = DEFAULT_TOPIC,
    bootstrap_server: str = DEFAULT_BOOTSTRAP_SERVER,
    poll_timeout_seconds: float = 1.0,
    max_empty_polls: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Consume provider feed events from local Kafka and run quality checks.

    Outputs:
    - data/quality_reports/kafka_provider_quality_summary.csv
    - data/quality_reports/kafka_provider_failed_events.csv
    - data/streaming/kafka_provider_consumed_events.jsonl
    """
    STREAMING_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    metadata = load_latest_run_metadata()

    run_id = metadata["run_id"]
    expected_count = int(metadata["published_count"])

    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap_server,
            "group.id": f"entityq-provider-quality-consumer-{uuid4()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )

    consumer.subscribe([topic])

    validation_results: list[dict[str, Any]] = []
    consumed_events: list[dict[str, Any]] = []
    empty_polls = 0

    print(f"Consuming events for run_id: {run_id}")
    print(f"Expected events: {expected_count}")

    try:
        while len(validation_results) < expected_count and empty_polls < max_empty_polls:
            message = consumer.poll(timeout=poll_timeout_seconds)

            if message is None:
                empty_polls += 1
                continue

            if message.error():
                raise KafkaException(message.error())

            event = json.loads(message.value().decode("utf-8"))

            if event.get("run_id") != run_id:
                continue

            consumed_events.append(event)
            validation_results.append(event_to_validation_result(event))

    finally:
        consumer.close()

    results = pd.DataFrame(validation_results)

    if results.empty:
        raise RuntimeError(
            "No events were consumed for the latest run_id. "
            "Check that Kafka is running and the producer published events."
        )

    summary = (
        results
        .groupby(["provider_name", "status"], dropna=False, as_index=False)
        .agg(
            event_count=("event_id", "count"),
            total_issues=("issue_count", "sum"),
        )
    )

    failed_events = results[results["status"] == "failed"].copy()

    summary.to_csv(
        QUALITY_REPORT_DIR / "kafka_provider_quality_summary.csv",
        index=False,
    )

    failed_events.to_csv(
        QUALITY_REPORT_DIR / "kafka_provider_failed_events.csv",
        index=False,
    )

    consumed_events_path = STREAMING_DIR / "kafka_provider_consumed_events.jsonl"

    with consumed_events_path.open("w", encoding="utf-8") as file:
        for event in consumed_events:
            file.write(json.dumps(event, default=str) + "\n")

    return summary, failed_events


if __name__ == "__main__":
    quality_summary, failed = consume_provider_feed_events()

    print("")
    print("Kafka provider feed consumption completed.")
    print("Reports written to:")
    print("- data/quality_reports/kafka_provider_quality_summary.csv")
    print("- data/quality_reports/kafka_provider_failed_events.csv")
    print("- data/streaming/kafka_provider_consumed_events.jsonl")
    print("")
    print("Kafka provider quality summary:")
    print(quality_summary)
    print("")
    print(f"Failed events: {len(failed)}")