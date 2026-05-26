from __future__ import annotations

from pathlib import Path

import pandas as pd


def create_stakeholder_report(
    report_dir: str | Path = "data/quality_reports",
) -> Path:
    """
    Create a markdown stakeholder report from the quality outputs.

    This report is designed for Product, Engineering, Data and business
    stakeholders who need a clear summary of data quality risks and actions.

    Inputs:
    - rule_results.csv
    - quality_scorecard.csv
    - table_quality_summary.csv

    Output:
    - stakeholder_report.md
    """
    report_dir = Path(report_dir)

    rule_results_path = report_dir / "rule_results.csv"
    scorecard_path = report_dir / "quality_scorecard.csv"
    table_summary_path = report_dir / "table_quality_summary.csv"

    if not rule_results_path.exists():
        raise FileNotFoundError("rule_results.csv not found. Run validation.py first.")

    if not scorecard_path.exists():
        raise FileNotFoundError("quality_scorecard.csv not found. Run metrics.py first.")

    if not table_summary_path.exists():
        raise FileNotFoundError("table_quality_summary.csv not found. Run metrics.py first.")

    rule_results = pd.read_csv(rule_results_path)
    scorecard = pd.read_csv(scorecard_path)
    table_summary = pd.read_csv(table_summary_path)

    worst_tables = table_summary.sort_values(
        "overall_quality_score",
        ascending=True,
    ).head(5)

    top_failed_rules = rule_results.sort_values(
        "failed_count",
        ascending=False,
    ).head(10)

    critical_rules = rule_results[
        (rule_results["severity"] == "Critical")
        & (rule_results["failed_count"] > 0)
    ].sort_values("failed_count", ascending=False)

    average_quality_score = round(table_summary["overall_quality_score"].mean(), 2)
    total_failed_records = int(table_summary["total_failed_records"].sum())
    total_rules = int(table_summary["total_rules"].sum())
    tables_checked = int(table_summary["table_name"].nunique())

    report_lines: list[str] = []

    report_lines.append("# EntityQ Stakeholder Data Quality Report")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append(
        "This report summarises the quality of synthetic financial entity, issuer, "
        "corporate hierarchy, KYC and third-party provider feed datasets."
    )
    report_lines.append("")
    report_lines.append(
        "The objective is to provide transparent quality metrics, identify material "
        "data risks, and recommend remediation actions for Product, Engineering, "
        "Data and business stakeholders."
    )
    report_lines.append("")
    report_lines.append("## Overall Quality Snapshot")
    report_lines.append("")
    report_lines.append(f"- Tables checked: **{tables_checked}**")
    report_lines.append(f"- Rules executed: **{total_rules}**")
    report_lines.append(f"- Average table quality score: **{average_quality_score}%**")
    report_lines.append(f"- Total failed record checks: **{total_failed_records:,}**")
    report_lines.append("")
    report_lines.append("## Table-Level Quality Summary")
    report_lines.append("")
    report_lines.append(table_summary.to_markdown(index=False))
    report_lines.append("")
    report_lines.append("## Lowest-Scoring Tables")
    report_lines.append("")
    report_lines.append(worst_tables.to_markdown(index=False))
    report_lines.append("")
    report_lines.append("## Quality Scorecard by Dimension")
    report_lines.append("")
    report_lines.append(scorecard.to_markdown(index=False))
    report_lines.append("")
    report_lines.append("## Top Failed Rules")
    report_lines.append("")
    report_lines.append(
        top_failed_rules[
            [
                "table_name",
                "rule_id",
                "dimension",
                "severity",
                "description",
                "failed_count",
                "pass_rate",
                "recommendation",
            ]
        ].to_markdown(index=False)
    )
    report_lines.append("")
    report_lines.append("## Critical Issues")
    report_lines.append("")

    if critical_rules.empty:
        report_lines.append("No critical rule failures were detected.")
    else:
        report_lines.append(
            critical_rules[
                [
                    "table_name",
                    "rule_id",
                    "dimension",
                    "description",
                    "failed_count",
                    "recommendation",
                ]
            ].to_markdown(index=False)
        )

    report_lines.append("")
    report_lines.append("## Recommended Remediation Actions")
    report_lines.append("")
    report_lines.append(
        "1. Prioritise critical referential integrity failures in issuer, hierarchy and KYC datasets."
    )
    report_lines.append(
        "2. Investigate duplicate master entity and issuer identifiers using survivorship rules."
    )
    report_lines.append(
        "3. Review stale active entity records and overdue high-risk KYC reviews."
    )
    report_lines.append(
        "4. Standardise provider country codes, entity types, statuses and confidence scores."
    )
    report_lines.append(
        "5. Move recurring checks into an automated scheduled workflow and publish quality scorecards regularly."
    )
    report_lines.append("")
    report_lines.append("## Stakeholder Interpretation")
    report_lines.append("")
    report_lines.append(
        "This framework treats data quality as an operational and product discipline, "
        "not just a one-off validation exercise. The scorecards show which datasets "
        "are reliable, which rules are failing, and which remediation actions should "
        "be prioritised."
    )
    report_lines.append("")
    report_lines.append(
        "The output can support conversations between Product, Engineering, Data, "
        "Operations and Risk teams by creating a shared view of data quality, ownership "
        "and improvement priorities."
    )

    report_path = report_dir / "stakeholder_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return report_path


if __name__ == "__main__":
    output_path = create_stakeholder_report()

    print("Stakeholder report created.")
    print(f"Output written to: {output_path}")