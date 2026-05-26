from __future__ import annotations

from pathlib import Path

import pandas as pd


def profile_table(table_name: str, df: pd.DataFrame) -> list[dict]:
    """
    Profile one dataframe column by column.

    For each column, we calculate:
    - row count
    - missing count
    - missing percentage
    - unique count
    - unique percentage
    - data type
    - top 5 most common values

    This gives us an early view of the data before applying rules.
    """
    results: list[dict] = []
    row_count = len(df)

    for column in df.columns:
        series = df[column]

        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))

        if row_count > 0:
            missing_pct = round((missing_count / row_count) * 100, 2)
            unique_pct = round((unique_count / row_count) * 100, 2)
        else:
            missing_pct = 0
            unique_pct = 0

        top_values = (
            series
            .astype(str)
            .value_counts(dropna=False)
            .head(5)
            .to_dict()
        )

        results.append(
            {
                "table_name": table_name,
                "column_name": column,
                "row_count": row_count,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": unique_count,
                "unique_pct": unique_pct,
                "dtype": str(series.dtype),
                "top_values": str(top_values),
            }
        )

    return results


def run_profiling(
    input_dir: str | Path = "data/raw",
    output_dir: str | Path = "data/quality_reports",
) -> pd.DataFrame:
    """
    Run profiling on every CSV file inside the raw data folder.

    The result is saved as:
    data/quality_reports/profile_summary.csv
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []

    csv_files = sorted(input_dir.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {input_dir}. Run data_generation.py first."
        )

    for file_path in csv_files:
        table_name = file_path.stem
        df = pd.read_csv(file_path)

        table_profile = profile_table(table_name, df)
        all_results.extend(table_profile)

    profile_df = pd.DataFrame(all_results)
    profile_df.to_csv(output_dir / "profile_summary.csv", index=False)

    return profile_df


if __name__ == "__main__":
    profile = run_profiling()
    print("Profiling completed.")
    print("Output written to: data/quality_reports/profile_summary.csv")
    print(profile.head(10))
