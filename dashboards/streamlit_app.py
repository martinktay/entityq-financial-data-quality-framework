from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


REPORT_DIR = Path("data/quality_reports")


st.set_page_config(
    page_title="EntityQ Data Quality Dashboard",
    layout="wide",
)


def load_report_file(file_name: str) -> pd.DataFrame:
    """
    Load a CSV report from the quality_reports folder.

    If the file does not exist, return an empty dataframe and show a warning.
    This makes the dashboard safer because it will not crash immediately if the
    pipeline has not been run yet.
    """
    file_path = REPORT_DIR / file_name

    if not file_path.exists():
        st.warning(
            f"{file_name} was not found. Run `python -m entityq.run_pipeline` first."
        )
        return pd.DataFrame()

    return pd.read_csv(file_path)


def show_dashboard_header() -> None:
    """
    Show the dashboard title and explanation.
    """
    st.title("EntityQ Data Quality Dashboard")
    st.caption(
        "Financial entity data quality monitoring for entity master, issuer, "
        "corporate hierarchy, KYC and third-party provider feed datasets."
    )


def show_table_summary(table_summary: pd.DataFrame) -> None:
    """
    Display table-level quality metrics.

    This gives stakeholders a quick answer to:
    - Which datasets are healthy?
    - Which datasets need attention?
    - What is the average quality score?
    """
    st.subheader("Table-Level Quality Summary")

    if table_summary.empty:
        st.info("No table quality summary available yet.")
        return

    total_tables = table_summary["table_name"].nunique()
    total_rules = int(table_summary["total_rules"].sum())
    average_score = round(table_summary["overall_quality_score"].mean(), 2)
    total_failed = int(table_summary["total_failed_records"].sum())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Tables Checked", total_tables)
    col2.metric("Rules Executed", total_rules)
    col3.metric("Average Quality Score", f"{average_score}%")
    col4.metric("Failed Record Checks", f"{total_failed:,}")

    st.dataframe(table_summary, use_container_width=True)

    chart = px.bar(
        table_summary,
        x="table_name",
        y="overall_quality_score",
        color="status",
        title="Overall Quality Score by Table",
        text="overall_quality_score",
    )

    st.plotly_chart(chart, use_container_width=True)


def show_dimension_scorecard(scorecard: pd.DataFrame) -> None:
    """
    Display quality scores by table and dimension.

    This helps identify whether the biggest issues are completeness, validity,
    timeliness, referential integrity or another quality dimension.
    """
    st.subheader("Quality Score by Dimension")

    if scorecard.empty:
        st.info("No quality scorecard available yet.")
        return

    st.dataframe(scorecard, use_container_width=True)

    chart = px.bar(
        scorecard,
        x="dimension",
        y="quality_score",
        color="table_name",
        barmode="group",
        title="Quality Score by Dimension and Table",
    )

    st.plotly_chart(chart, use_container_width=True)


def show_failed_rules(rule_results: pd.DataFrame) -> None:
    """
    Display failed data quality rules.

    This section is useful for engineering and data teams because it shows the
    exact rules that failed and the recommended remediation actions.
    """
    st.subheader("Failed Data Quality Rules")

    if rule_results.empty:
        st.info("No rule results available yet.")
        return

    failed_rules = rule_results[rule_results["failed_count"] > 0].copy()
    failed_rules = failed_rules.sort_values("failed_count", ascending=False)

    severity_filter = st.multiselect(
        "Filter by severity",
        options=sorted(failed_rules["severity"].dropna().unique()),
        default=sorted(failed_rules["severity"].dropna().unique()),
    )

    dimension_filter = st.multiselect(
        "Filter by quality dimension",
        options=sorted(failed_rules["dimension"].dropna().unique()),
        default=sorted(failed_rules["dimension"].dropna().unique()),
    )

    filtered = failed_rules[
        failed_rules["severity"].isin(severity_filter)
        & failed_rules["dimension"].isin(dimension_filter)
    ]

    st.dataframe(
        filtered[
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
        ],
        use_container_width=True,
    )

    chart = px.bar(
        filtered.head(15),
        x="rule_id",
        y="failed_count",
        color="severity",
        title="Top Failed Rules",
        hover_data=["table_name", "description"],
    )

    st.plotly_chart(chart, use_container_width=True)


def show_critical_issues(rule_results: pd.DataFrame) -> None:
    """
    Highlight critical data quality issues.

    Critical issues usually affect dataset usability, linkage, or downstream
    financial workflows.
    """
    st.subheader("Critical Issues")

    if rule_results.empty:
        st.info("No rule results available yet.")
        return

    critical = rule_results[
        (rule_results["severity"] == "Critical")
        & (rule_results["failed_count"] > 0)
    ].sort_values("failed_count", ascending=False)

    if critical.empty:
        st.success("No critical data quality failures detected.")
        return

    st.dataframe(
        critical[
            [
                "table_name",
                "rule_id",
                "dimension",
                "description",
                "failed_count",
                "recommendation",
            ]
        ],
        use_container_width=True,
    )


def show_anomaly_candidates(anomalies: pd.DataFrame) -> None:
    """
    Display AI/ML anomaly candidates.

    These are not automatic errors. They are unusual records that should be
    reviewed by data analysts or data quality owners.
    """
    st.subheader("AI/ML Anomaly Candidates")

    if anomalies.empty:
        st.info("No anomaly results available yet.")
        return

    columns_to_show = [
        "entity_id",
        "legal_name",
        "country_code",
        "entity_type",
        "status",
        "source_system",
        "anomaly_score",
    ]

    available_columns = [
        column for column in columns_to_show if column in anomalies.columns
    ]

    st.dataframe(
        anomalies[available_columns].head(100),
        use_container_width=True,
    )

    if "source_system" in anomalies.columns:
        source_counts = (
            anomalies["source_system"]
            .value_counts()
            .reset_index()
        )

        source_counts.columns = ["source_system", "anomaly_count"]

        chart = px.bar(
            source_counts,
            x="source_system",
            y="anomaly_count",
            title="Anomaly Candidates by Source System",
        )

        st.plotly_chart(chart, use_container_width=True)


def show_stakeholder_report_preview() -> None:
    """
    Show a preview of the stakeholder markdown report.
    """
    st.subheader("Stakeholder Report Preview")

    report_path = REPORT_DIR / "stakeholder_report.md"

    if not report_path.exists():
        st.info("stakeholder_report.md not found yet.")
        return

    report_text = report_path.read_text(encoding="utf-8")

    st.markdown(report_text)


def main() -> None:
    """
    Run the Streamlit dashboard.
    """
    show_dashboard_header()

    table_summary = load_report_file("table_quality_summary.csv")
    scorecard = load_report_file("quality_scorecard.csv")
    rule_results = load_report_file("rule_results.csv")
    anomalies = load_report_file("entity_anomalies.csv")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Executive Summary",
            "Scorecard",
            "Failed Rules",
            "Anomalies",
            "Stakeholder Report",
        ]
    )

    with tab1:
        show_table_summary(table_summary)
        show_critical_issues(rule_results)

    with tab2:
        show_dimension_scorecard(scorecard)

    with tab3:
        show_failed_rules(rule_results)

    with tab4:
        show_anomaly_candidates(anomalies)

    with tab5:
        show_stakeholder_report_preview()


if __name__ == "__main__":
    main()