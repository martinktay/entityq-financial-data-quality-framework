# SQL Data Quality Report: counterparty_trade_links

## Executive Summary

- SQL rules executed: 18
- Rules with failures: 17
- Failed record exceptions generated: 2,902
- Critical rules with failures: 2
- High-severity rules with failures: 9

## Why This Matters

This SQL layer demonstrates how EntityQ can validate a newly onboarded dirty financial dataset using transparent SQL checks. The dataset links trades to counterparties, issuers, instruments, KYC status, provider confidence scores and reference data attributes. These checks help identify issues that could affect client onboarding, compliance, settlement, counterparty risk, issuer classification and reporting workflows.

## Top SQL Rule Failures

| rule_id          | severity   | dimension             | description                                                                       |   failed_count |   failure_rate_pct |
|:-----------------|:-----------|:----------------------|:----------------------------------------------------------------------------------|---------------:|-------------------:|
| SQL_TIME_001     | Medium     | Timeliness            | Reference data should be verified within the last 365 days.                       |           1719 |              85.95 |
| SQL_PROVIDER_002 | Medium     | Accuracy              | Provider confidence score should not be below 0.70.                               |            429 |              21.45 |
| SQL_TRADE_002    | Critical   | Uniqueness            | Trade ID must be unique.                                                          |             92 |               4.6  |
| SQL_KYC_001      | Critical   | Compliance            | High-risk counterparties should have approved KYC.                                |             78 |               3.9  |
| SQL_CP_001       | High       | Completeness          | Counterparty entity ID must not be missing.                                       |             73 |               3.65 |
| SQL_REVIEW_001   | High       | Risk Review           | Large trades involving high-risk or incomplete-KYC counterparties require review. |             66 |               3.3  |
| SQL_ISSUER_001   | High       | Referential Integrity | Issuer ID should resolve to a known issuer reference record.                      |             58 |               2.9  |
| SQL_REF_002      | High       | Validity              | Risk country must be a valid supported country code.                              |             55 |               2.75 |
| SQL_ENTITY_001   | Medium     | Validity              | LEI should follow a 20-character alphanumeric pattern.                            |             46 |               2.3  |
| SQL_DATE_002     | High       | Validity              | Settlement date should not be before trade date.                                  |             44 |               2.2  |

## Outputs

- data/quality_reports/sql_counterparty_trade_rule_results.csv
- data/quality_reports/sql_counterparty_trade_failed_records.csv
- data/quality_reports/sql_counterparty_trade_report.md
