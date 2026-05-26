from __future__ import annotations

from pathlib import Path

import pandas as pd


def assign_status(score: float) -> str:
    """
    Convert a numeric quality score into a simple status.

    This makes the scorecard easier for non-technical stakeholders to read.

    Example:
    95.0 becomes "Good"
    84.0 becomes "Monitor"
    70.0 becomes "Needs Attention"
    """
    if score >= 90:
        return "Good"

    if score >= 80:
        return "Monitor"

    return "Needs Attention"


def run_metrics(
    rule_results: pd.DataFrame | None = None,
    output_dir: str | Path = "data/quality_reports",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert rule-level validation results into quality scorecards.

    Inputs:
    - rule_results.csv from validation.py

    Outputs:
    - quality_scorecard.csv
    - table_quality_summary.csv
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if rule_results is None:
        rule_results_path = output_dir / "rule_results.csv"

        if not rule_results_path.exists():
            raise FileNotFoundError(
                "rule_results.csv was not found. Run validation.py first."
            )

        rule_results = pd.read_csv(rule_results_path)

    quality_scorecard = (
        rule_results
        .groupby(["table_name", "dimension"], as_index=False)
        .agg(
            rule_count=("rule_id", "count"),
            total_records_checked=("total_count", "sum"),
            total_failed_records=("failed_count", "sum"),
            average_pass_rate=("pass_rate", "mean"),
        )
    )

    quality_scorecard["quality_score"] = (
        quality_scorecard["average_pass_rate"] * 100
    ).round(2)

    quality_scorecard["status"] = quality_scorecard["quality_score"].apply(assign_status)

    table_quality_summary = (
        quality_scorecard
        .groupby("table_name", as_index=False)
        .agg(
            dimensions_checked=("dimension", "nunique"),
            total_rules=("rule_count", "sum"),
            total_failed_records=("total_failed_records", "sum"),
            overall_quality_score=("quality_score", "mean"),
        )
    )

    table_quality_summary["overall_quality_score"] = (
        table_quality_summary["overall_quality_score"].round(2)
    )

    table_quality_summary["status"] = table_quality_summary[
        "overall_quality_score"
    ].apply(assign_status)

    quality_scorecard.to_csv(output_dir / "quality_scorecard.csv", index=False)
    table_quality_summary.to_csv(output_dir / "table_quality_summary.csv", index=False)

    return quality_scorecard, table_quality_summary


if __name__ == "__main__":
    scorecard, table_summary = run_metrics()

    print("Metrics completed.")
    print("Outputs written to:")
    print("- data/quality_reports/quality_scorecard.csv")
    print("- data/quality_reports/table_quality_summary.csv")

    print("\nTable quality summary:")
    print(table_summary)