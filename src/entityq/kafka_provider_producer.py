from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from confluent_kafka import Producer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
STREAMING_DIR = PROJECT_ROOT / "data" / "streaming"

DEFAULT_TOPIC = "provider-feed-raw"
DEFAULT_BOOTSTRAP_SERVER = "localhost:9092"


def delivery_report(error: Exception | None, message: Any) -> None:
    """
    Callback used by Kafka producer after a message is delivered.

    If delivery fails, it prints the error.
    If delivery succeeds, it prints the topic, partition and offset.
    """
    if error is not None:
        print(f"Delivery failed: {error}")
    else:
        print(
            "Delivered event to "
            f"{message.topic()} [{message.partition()}] at offset {message.offset()}"
        )


def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Convert pandas NaN values into None so the message can be valid JSON.
    """
    cleaned: dict[str, Any] = {}

    for key, value in record.items():
        if pd.isna(value):
            cleaned[key] = None
        else:
            cleaned[key] = value

    return cleaned


def build_kafka_event(
    record: dict[str, Any],
    sequence_number: int,
    run_id: str,
) -> dict[str, Any]:
    """
    Convert one provider feed row into a Kafka event.

    The run_id allows the consumer to identify events created by the current run.
    """
    provider_record_id = record.get("provider_record_id")

    return {
        "event_id": str(uuid4()),
        "run_id": run_id,
        "event_type": "provider_record_received",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "sequence_number": sequence_number,
        "key": provider_record_id,
        "payload": record,
    }


def publish_provider_feed_events(
    input_dir: str | Path = RAW_DATA_DIR,
    topic: str = DEFAULT_TOPIC,
    bootstrap_server: str = DEFAULT_BOOTSTRAP_SERVER,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Publish provider feed records into a local Kafka topic.

    Input:
    - data/raw/provider_feed.csv

    Kafka topic:
    - provider-feed-raw

    Metadata output:
    - data/streaming/kafka_run_metadata.json
    """
    input_dir = Path(input_dir)
    STREAMING_DIR.mkdir(parents=True, exist_ok=True)

    provider_feed_path = input_dir / "provider_feed.csv"

    if not provider_feed_path.exists():
        raise FileNotFoundError(
            "provider_feed.csv was not found. Run `python -m entityq.run_pipeline` first."
        )

    provider_feed = pd.read_csv(provider_feed_path).head(limit)

    producer = Producer(
        {
            "bootstrap.servers": bootstrap_server,
            "client.id": "entityq-provider-feed-producer",
        }
    )

    run_id = str(uuid4())
    published_count = 0

    for sequence_number, raw_record in enumerate(
        provider_feed.to_dict(orient="records"),
        start=1,
    ):
        record = clean_record(raw_record)
        event = build_kafka_event(record, sequence_number, run_id)

        message_key = str(event["key"]) if event["key"] is not None else event["event_id"]
        message_value = json.dumps(event, default=str)

        producer.produce(
            topic=topic,
            key=message_key,
            value=message_value,
            callback=delivery_report,
        )

        producer.poll(0)
        published_count += 1

    producer.flush()

    metadata = {
        "run_id": run_id,
        "topic": topic,
        "bootstrap_server": bootstrap_server,
        "published_count": published_count,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    metadata_path = STREAMING_DIR / "kafka_run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metadata


if __name__ == "__main__":
    result = publish_provider_feed_events()

    print("")
    print("Kafka provider feed publishing completed.")
    print(f"Run ID: {result['run_id']}")
    print(f"Topic: {result['topic']}")
    print(f"Published events: {result['published_count']}")
    print("Metadata written to: data/streaming/kafka_run_metadata.json")