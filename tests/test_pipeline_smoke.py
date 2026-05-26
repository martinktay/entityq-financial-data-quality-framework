from pathlib import Path

import pandas as pd

from entityq.anomaly_detection import run_anomaly_detection
from entityq.data_generation import generate_all
from entityq.metrics import run_metrics
from entityq.profiling import run_profiling
from entityq.reporting import create_stakeholder_report
from entityq.validation import run_validation


def test_core_pipeline_runs_successfully(tmp_path: Path) -> None:
    """
    Smoke test for the full EntityQ pipeline.

    This test uses a temporary folder instead of the real data folder.
    That makes the test safe and repeatable.
    """
    raw_dir = tmp_path / "raw"
    report_dir = tmp_path / "quality_reports"

    generated_data = generate_all(raw_dir, entity_count=300, seed=123)
    profile = run_profiling(raw_dir, report_dir)
    rule_results = run_validation(raw_dir, report_dir)
    scorecard, table_summary = run_metrics(rule_results, report_dir)
    anomalies = run_anomaly_detection(raw_dir, report_dir)
    stakeholder_report = create_stakeholder_report(report_dir)

    assert generated_data
    assert not profile.empty
    assert not rule_results.empty
    assert not scorecard.empty
    assert not table_summary.empty
    assert not anomalies.empty
    assert stakeholder_report.exists()

    assert (raw_dir / "entities.csv").exists()
    assert (raw_dir / "issuers.csv").exists()
    assert (raw_dir / "entity_hierarchy.csv").exists()
    assert (raw_dir / "kyc_attributes.csv").exists()
    assert (raw_dir / "provider_feed.csv").exists()

    assert (report_dir / "profile_summary.csv").exists()
    assert (report_dir / "rule_results.csv").exists()
    assert (report_dir / "quality_scorecard.csv").exists()
    assert (report_dir / "table_quality_summary.csv").exists()
    assert (report_dir / "entity_anomalies.csv").exists()
    assert (report_dir / "stakeholder_report.md").exists()


def test_quality_scorecard_has_expected_columns(tmp_path: Path) -> None:
    """
    Check that the metrics layer produces the expected scorecard structure.
    """
    raw_dir = tmp_path / "raw"
    report_dir = tmp_path / "quality_reports"

    generate_all(raw_dir, entity_count=300, seed=456)
    run_profiling(raw_dir, report_dir)
    rule_results = run_validation(raw_dir, report_dir)
    scorecard, table_summary = run_metrics(rule_results, report_dir)

    expected_scorecard_columns = {
        "table_name",
        "dimension",
        "rule_count",
        "total_records_checked",
        "total_failed_records",
        "average_pass_rate",
        "quality_score",
        "status",
    }

    expected_summary_columns = {
        "table_name",
        "dimensions_checked",
        "total_rules",
        "total_failed_records",
        "overall_quality_score",
        "status",
    }

    assert expected_scorecard_columns.issubset(set(scorecard.columns))
    assert expected_summary_columns.issubset(set(table_summary.columns))


def test_validation_catches_known_quality_issues(tmp_path: Path) -> None:
    """
    Check that validation rules actually detect failures.

    Since the data generator deliberately injects messy data, we expect
    at least some rules to fail.
    """
    raw_dir = tmp_path / "raw"
    report_dir = tmp_path / "quality_reports"

    generate_all(raw_dir, entity_count=300, seed=789)
    rule_results = run_validation(raw_dir, report_dir)

    total_failed = int(rule_results["failed_count"].sum())

    assert total_failed > 0
    assert "Critical" in set(rule_results["severity"])
    assert "Completeness" in set(rule_results["dimension"])
    assert "Validity" in set(rule_results["dimension"])
    assert "Referential Integrity" in set(rule_results["dimension"])