from __future__ import annotations

from pathlib import Path

from entityq.anomaly_detection import run_anomaly_detection
from entityq.data_generation import generate_all
from entityq.metrics import run_metrics
from entityq.profiling import run_profiling
from entityq.reporting import create_stakeholder_report
from entityq.validation import run_validation


def main() -> None:
    """
    Run the full EntityQ data quality pipeline.

    Pipeline stages:
    1. Generate synthetic messy financial entity data.
    2. Profile the raw datasets.
    3. Run validation rules.
    4. Convert validation results into quality scorecards.
    5. Run anomaly detection on entity records.
    6. Produce a stakeholder-facing markdown report.
    """
    raw_dir = Path("data/raw")
    report_dir = Path("data/quality_reports")

    print("1/6 Generating synthetic messy financial entity data...")
    generate_all(raw_dir, entity_count=5000)

    print("2/6 Running data profiling...")
    run_profiling(raw_dir, report_dir)

    print("3/6 Running data quality validation rules...")
    rule_results = run_validation(raw_dir, report_dir)

    print("4/6 Creating quality scorecards...")
    run_metrics(rule_results, report_dir)

    print("5/6 Running AI/ML-enabled anomaly detection...")
    run_anomaly_detection(raw_dir, report_dir)

    print("6/6 Creating stakeholder report...")
    report_path = create_stakeholder_report(report_dir)

    print("")
    print("Pipeline complete.")
    print(f"Raw datasets written to: {raw_dir}")
    print(f"Quality reports written to: {report_dir}")
    print(f"Stakeholder report written to: {report_path}")


if __name__ == "__main__":
    main()