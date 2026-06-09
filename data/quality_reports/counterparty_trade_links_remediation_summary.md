# Counterparty Trade Links Remediation Summary

## Executive Summary

- Total incoming records: 2,000
- Records with at least one issue: 830
- Records accepted into curated output: 1,518
- Records quarantined for review: 482
- Curated acceptance rate: 75.9%
- Quarantine rate: 24.1%

## Remediation Approach

The remediation layer applies safe standardisation rules where the intended value is clear, such as mapping `EURO` to `EUR` and `UK` to `GB`.

Records with blocking issues are not forced into the curated dataset. They are quarantined for analyst, reference data, KYC, risk, or operations review.

## Top Remediation Flags

| count                             |   count |
|:----------------------------------|--------:|
| low_provider_confidence_score     |     429 |
| duplicate_trade_id                |      92 |
| high_risk_incomplete_kyc          |      78 |
| missing_counterparty_entity_id    |      73 |
| invalid_or_orphan_issuer_id       |      58 |
| invalid_risk_country              |      46 |
| settlement_before_trade_date      |      44 |
| invalid_notional_amount           |      41 |
| weak_counterparty_name            |      36 |
| invalid_instrument_type           |      35 |
| invalid_provider_confidence_score |      30 |
| invalid_currency                  |      26 |
| invalid_trade_date                |      17 |

## Outputs

- data/curated/counterparty_trade_links_curated.csv
- data/curated/counterparty_trade_links_quarantine.csv
- data/quality_reports/counterparty_trade_links_remediation_summary.md
