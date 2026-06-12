from __future__ import annotations

from entityq.counterparty_trade_remediation import run_remediation
from entityq.new_dataset_onboarding import onboard_dataset
from entityq.run_pipeline import main as run_core_pipeline
from entityq.sql_quality_runner import run_sql_quality_checks


def main() -> None:
    """
    Run the full EntityQ demo workflow.

    This combines the core synthetic data pipeline with the newer
    counterparty dataset onboarding, SQL validation, and remediation flows.
    """
    # Kafka remains a separate streaming demo because it requires a running broker.
    print("Running core EntityQ pipeline...")
    run_core_pipeline()

    print("")
    print("Running counterparty dataset onboarding...")
    onboard_dataset("counterparty_trade_links")

    print("")
    print("Running counterparty SQL quality checks...")
    run_sql_quality_checks()

    print("")
    print("Running counterparty remediation workflow...")
    run_remediation()

    print("")
    print("Full EntityQ demo complete.")


if __name__ == "__main__":
    main()