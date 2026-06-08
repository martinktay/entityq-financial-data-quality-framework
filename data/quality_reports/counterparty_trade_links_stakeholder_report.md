# New Dataset Onboarding Report: counterparty_trade_links

## Executive Summary

- Total rows profiled: 2,000
- Total columns profiled: 25
- Validation rules executed: 19
- Rules with failures: 16
- Failed record exceptions generated: 2,840
- Critical rules with failures: 2
- High-severity rules with failures: 8

## What This Dataset Represents

This dataset simulates trade-linked counterparty reference data. It connects trade records to counterparties, issuers, instruments, KYC status, risk ratings, provider confidence scores and source systems. This is useful for demonstrating how poor entity/reference data can affect financial workflows such as client onboarding, KYC, counterparty risk, issuer classification, settlement and reporting.

## Top Data Quality Issues

| rule_id      | severity   | description                                                  |   failed_count |   failure_rate_pct |
|:-------------|:-----------|:-------------------------------------------------------------|---------------:|-------------------:|
| TIME_001     | Medium     | Reference data should be verified within the last 365 days.  |           1723 |              86.15 |
| PROVIDER_002 | Medium     | Provider confidence score should not be below 0.70.          |            429 |              21.45 |
| TRADE_002    | Critical   | Trade ID must be unique.                                     |             92 |               4.6  |
| KYC_001      | Critical   | High-risk counterparties should have approved KYC.           |             78 |               3.9  |
| CP_001       | High       | Counterparty entity ID must not be missing.                  |             73 |               3.65 |
| ISSUER_002   | High       | Issuer ID should resolve to a known issuer reference record. |             58 |               2.9  |
| REF_002      | High       | Risk country must be a valid supported country code.         |             55 |               2.75 |
| ENTITY_001   | Medium     | LEI should follow a 20-character alphanumeric pattern.       |             46 |               2.3  |
| DATE_002     | High       | Settlement date should not be before trade date.             |             44 |               2.2  |
| REF_001      | High       | Currency must be an approved ISO-style currency code.        |             43 |               2.15 |

## Recommended Actions

1. Prioritise critical issues such as duplicate trade IDs and high-risk counterparties with incomplete KYC.
2. Route invalid issuer and counterparty references to reference data remediation queues.
3. Standardise invalid currency, country and instrument taxonomy values.
4. Review low-confidence provider records before using them in curated data products.
5. Refresh stale reference records older than 365 days.

## Output Files

- data/quality_reports/counterparty_trade_links_column_profile.csv
- data/quality_reports/counterparty_trade_links_rule_results.csv
- data/quality_reports/counterparty_trade_links_failed_records.csv
- data/quality_reports/counterparty_trade_links_stakeholder_report.md
