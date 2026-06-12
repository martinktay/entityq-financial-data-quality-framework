from __future__ import annotations

from pathlib import Path

from entityq.new_dataset_onboarding import get_dataset_config, load_registry


def test_dataset_registry_loads_counterparty_dataset() -> None:
    registry = load_registry()

    assert "datasets" in registry
    assert "counterparty_trade_links" in registry["datasets"]


def test_counterparty_dataset_config_is_registered() -> None:
    dataset_config = get_dataset_config("counterparty_trade_links")

    assert dataset_config["primary_key"] == "trade_id"
    assert dataset_config["file_path"] == "data/incoming/counterparty_trade_links.csv"


def test_incoming_counterparty_dataset_exists() -> None:
    assert Path("data/incoming/counterparty_trade_links.csv").exists()