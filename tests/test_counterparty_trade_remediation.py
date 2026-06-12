from __future__ import annotations

from pathlib import Path

import pandas as pd

from entityq import counterparty_trade_remediation as remediation


def test_remediation_creates_curated_and_quarantine_outputs(tmp_path: Path, monkeypatch) -> None:
    curated_dir = tmp_path / "curated"
    report_dir = tmp_path / "quality_reports"

    monkeypatch.setattr(remediation, "CURATED_DIR", curated_dir)
    monkeypatch.setattr(remediation, "QUALITY_REPORT_DIR", report_dir)
    monkeypatch.setattr(remediation, "CURATED_OUTPUT_PATH", curated_dir / "counterparty_trade_links_curated.csv")
    monkeypatch.setattr(remediation, "QUARANTINE_OUTPUT_PATH", curated_dir / "counterparty_trade_links_quarantine.csv")
    monkeypatch.setattr(remediation, "REMEDIATION_SUMMARY_PATH", report_dir / "counterparty_trade_links_remediation_summary.md")

    remediation.run_remediation()

    curated_path = curated_dir / "counterparty_trade_links_curated.csv"
    quarantine_path = curated_dir / "counterparty_trade_links_quarantine.csv"
    summary_path = report_dir / "counterparty_trade_links_remediation_summary.md"

    assert curated_path.exists()
    assert quarantine_path.exists()
    assert summary_path.exists()

    curated = pd.read_csv(curated_path)
    quarantine = pd.read_csv(quarantine_path)

    assert len(curated) + len(quarantine) > 0
    assert "curation_status" in curated.columns or "curation_status" in quarantine.columns