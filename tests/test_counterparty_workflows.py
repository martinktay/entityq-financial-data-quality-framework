from __future__ import annotations

from pathlib import Path

import pandas as pd

from entityq import counterparty_trade_remediation as remediation
from entityq import new_dataset_onboarding as onboarding
from entityq import run_full_demo
from entityq import sql_quality_runner as sql_runner


def test_counterparty_onboarding_writes_reports(tmp_path: Path, monkeypatch) -> None:
    report_dir = tmp_path / "quality_reports"
    monkeypatch.setattr(onboarding, "QUALITY_REPORT_DIR", report_dir)

    onboarding.onboard_dataset("counterparty_trade_links")

    rule_results = report_dir / "counterparty_trade_links_rule_results.csv"
    failed_records = report_dir / "counterparty_trade_links_failed_records.csv"
    stakeholder_report = report_dir / "counterparty_trade_links_stakeholder_report.md"
    column_profile = report_dir / "counterparty_trade_links_column_profile.csv"

    assert column_profile.exists()
    assert rule_results.exists()
    assert failed_records.exists()
    assert stakeholder_report.exists()

    loaded = pd.read_csv(rule_results)
    assert not loaded.empty
    assert {"dataset_name", "rule_id", "failed_count"}.issubset(loaded.columns)


def test_sql_quality_runner_writes_reports(tmp_path: Path, monkeypatch) -> None:
    report_dir = tmp_path / "quality_reports"
    monkeypatch.setattr(sql_runner, "QUALITY_REPORT_DIR", report_dir)

    sql_runner.run_sql_quality_checks()

    rule_results = report_dir / "sql_counterparty_trade_rule_results.csv"
    failed_records = report_dir / "sql_counterparty_trade_failed_records.csv"
    report = report_dir / "sql_counterparty_trade_report.md"

    assert rule_results.exists()
    assert failed_records.exists()
    assert report.exists()

    loaded = pd.read_csv(rule_results)
    assert not loaded.empty
    assert {"rule_id", "status", "failed_count"}.issubset(loaded.columns)


def test_remediation_writes_curated_and_quarantine_outputs(tmp_path: Path, monkeypatch) -> None:
    curated_dir = tmp_path / "curated"
    report_dir = tmp_path / "quality_reports"

    monkeypatch.setattr(remediation, "CURATED_DIR", curated_dir)
    monkeypatch.setattr(remediation, "QUALITY_REPORT_DIR", report_dir)
    monkeypatch.setattr(remediation, "CURATED_OUTPUT_PATH", curated_dir / "counterparty_trade_links_curated.csv")
    monkeypatch.setattr(remediation, "QUARANTINE_OUTPUT_PATH", curated_dir / "counterparty_trade_links_quarantine.csv")
    monkeypatch.setattr(remediation, "REMEDIATION_SUMMARY_PATH", report_dir / "counterparty_trade_links_remediation_summary.md")

    remediation.run_remediation()

    assert (curated_dir / "counterparty_trade_links_curated.csv").exists()
    assert (curated_dir / "counterparty_trade_links_quarantine.csv").exists()
    assert (report_dir / "counterparty_trade_links_remediation_summary.md").exists()


def test_full_demo_calls_each_stage(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(run_full_demo, "run_core_pipeline", lambda: calls.append("core"))
    monkeypatch.setattr(run_full_demo, "onboard_dataset", lambda dataset_name: calls.append(f"onboard:{dataset_name}"))
    monkeypatch.setattr(run_full_demo, "run_sql_quality_checks", lambda: calls.append("sql"))
    monkeypatch.setattr(run_full_demo, "run_remediation", lambda: calls.append("remediation"))

    run_full_demo.main()

    assert calls == ["core", "onboard:counterparty_trade_links", "sql", "remediation"]