from __future__ import annotations

from pathlib import Path

import pandas as pd

from entityq import sql_quality_runner as sql_runner


def test_sql_rule_parser_finds_counterparty_rules() -> None:
    sql_text = sql_runner.read_sql_file()
    rules = sql_runner.parse_sql_rules(sql_text)

    assert rules
    assert {"rule_id", "severity", "dimension", "query"}.issubset(rules[0].keys())


def test_sql_quality_runner_creates_outputs(tmp_path: Path, monkeypatch) -> None:
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