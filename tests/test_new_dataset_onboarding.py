from __future__ import annotations

from pathlib import Path

import pandas as pd

from entityq import new_dataset_onboarding as onboarding


def test_onboarding_creates_report_files(tmp_path: Path, monkeypatch) -> None:
    report_dir = tmp_path / "quality_reports"
    monkeypatch.setattr(onboarding, "QUALITY_REPORT_DIR", report_dir)

    onboarding.onboard_dataset("counterparty_trade_links")

    column_profile = report_dir / "counterparty_trade_links_column_profile.csv"
    rule_results = report_dir / "counterparty_trade_links_rule_results.csv"
    failed_records = report_dir / "counterparty_trade_links_failed_records.csv"
    stakeholder_report = report_dir / "counterparty_trade_links_stakeholder_report.md"

    assert column_profile.exists()
    assert rule_results.exists()
    assert failed_records.exists()
    assert stakeholder_report.exists()

    loaded = pd.read_csv(rule_results)
    assert not loaded.empty
    assert {"dataset_name", "rule_id", "failed_count"}.issubset(loaded.columns)