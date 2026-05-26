# EntityQ Stakeholder Data Quality Report

## Executive Summary

This report summarises the quality of synthetic financial entity, issuer, corporate hierarchy, KYC and third-party provider feed datasets.

The objective is to provide transparent quality metrics, identify material data risks, and recommend remediation actions for Product, Engineering, Data and business stakeholders.

## Overall Quality Snapshot

- Tables checked: **5**
- Rules executed: **27**
- Average table quality score: **90.41%**
- Total failed record checks: **9,798**

## Table-Level Quality Summary

| table_name       |   dimensions_checked |   total_rules |   total_failed_records |   overall_quality_score | status   |
|:-----------------|---------------------:|--------------:|-----------------------:|------------------------:|:---------|
| entities         |                    4 |             9 |                   4301 |                   80.64 | Monitor  |
| entity_hierarchy |                    3 |             5 |                    401 |                   96.19 | Good     |
| issuers          |                    4 |             5 |                    202 |                   97.42 | Good     |
| kyc_attributes   |                    3 |             4 |                   4138 |                   82.72 | Monitor  |
| provider_feed    |                    4 |             4 |                    756 |                   95.1  | Good     |

## Lowest-Scoring Tables

| table_name       |   dimensions_checked |   total_rules |   total_failed_records |   overall_quality_score | status   |
|:-----------------|---------------------:|--------------:|-----------------------:|------------------------:|:---------|
| entities         |                    4 |             9 |                   4301 |                   80.64 | Monitor  |
| kyc_attributes   |                    3 |             4 |                   4138 |                   82.72 | Monitor  |
| provider_feed    |                    4 |             4 |                    756 |                   95.1  | Good     |
| entity_hierarchy |                    3 |             5 |                    401 |                   96.19 | Good     |
| issuers          |                    4 |             5 |                    202 |                   97.42 | Good     |

## Quality Scorecard by Dimension

| table_name       | dimension             |   rule_count |   total_records_checked |   total_failed_records |   average_pass_rate |   quality_score | status          |
|:-----------------|:----------------------|-------------:|------------------------:|-----------------------:|--------------------:|----------------:|:----------------|
| entities         | Completeness          |            3 |                   15300 |                    185 |             0.9879  |           98.79 | Good            |
| entities         | Timeliness            |            1 |                    5100 |                   3611 |             0.292   |           29.2  | Needs Attention |
| entities         | Uniqueness            |            1 |                    5100 |                    200 |             0.9608  |           96.08 | Good            |
| entities         | Validity              |            4 |                   20400 |                    305 |             0.98505 |           98.5  | Good            |
| entity_hierarchy | Hierarchy Integrity   |            1 |                    2020 |                     61 |             0.9698  |           96.98 | Good            |
| entity_hierarchy | Referential Integrity |            2 |                    4040 |                     49 |             0.98785 |           98.78 | Good            |
| entity_hierarchy | Validity              |            2 |                    4040 |                    291 |             0.92795 |           92.8  | Good            |
| issuers          | Completeness          |            2 |                    3030 |                     92 |             0.96965 |           96.96 | Good            |
| issuers          | Referential Integrity |            1 |                    1515 |                     26 |             0.9828  |           98.28 | Good            |
| issuers          | Uniqueness            |            1 |                    1515 |                     30 |             0.9802  |           98.02 | Good            |
| issuers          | Validity              |            1 |                    1515 |                     54 |             0.9644  |           96.44 | Good            |
| kyc_attributes   | Referential Integrity |            1 |                    4250 |                     64 |             0.9849  |           98.49 | Good            |
| kyc_attributes   | Timeliness            |            2 |                    8500 |                   3870 |             0.5447  |           54.47 | Needs Attention |
| kyc_attributes   | Validity              |            1 |                    4250 |                    204 |             0.952   |           95.2  | Good            |
| provider_feed    | Completeness          |            1 |                    3857 |                     78 |             0.9798  |           97.98 | Good            |
| provider_feed    | Consistency           |            1 |                    3857 |                      0 |             1       |          100    | Good            |
| provider_feed    | Uniqueness            |            1 |                    3857 |                    114 |             0.9704  |           97.04 | Good            |
| provider_feed    | Validity              |            1 |                    3857 |                    564 |             0.8538  |           85.38 | Monitor         |

## Top Failed Rules

| table_name       | rule_id   | dimension    | severity   | description                                                                      |   failed_count |   pass_rate | recommendation                                                    |
|:-----------------|:----------|:-------------|:-----------|:---------------------------------------------------------------------------------|---------------:|------------:|:------------------------------------------------------------------|
| entities         | ENT-008   | Timeliness   | Medium     | active entity records should be verified within the last 365 days.               |           3611 |      0.292  | Prioritise stale active entities for review.                      |
| kyc_attributes   | KYC-004   | Timeliness   | High       | next_review_due_date should not be overdue.                                      |           2661 |      0.3739 | Trigger remediation workflow for overdue KYC reviews.             |
| kyc_attributes   | KYC-003   | Timeliness   | Critical   | High and Critical risk counterparties should have been reviewed within 365 days. |           1209 |      0.7155 | Prioritise stale high-risk counterparties for review.             |
| provider_feed    | PRV-003   | Validity     | Medium     | confidence_score must be between 0 and 1.                                        |            564 |      0.8538 | Standardise provider confidence scores and reject invalid values. |
| entity_hierarchy | HIER-004  | Validity     | High       | ownership_percentage must be between 0 and 100.                                  |            270 |      0.8663 | Review ownership percentages outside the valid range.             |
| kyc_attributes   | KYC-002   | Validity     | High       | risk_rating must be Low, Medium, High, or Critical.                              |            204 |      0.952  | Map invalid risk ratings to the approved risk taxonomy.           |
| entities         | ENT-002   | Uniqueness   | Critical   | entity_id must be unique.                                                        |            200 |      0.9608 | Investigate duplicate entity IDs and apply survivorship rules.    |
| entities         | ENT-004   | Validity     | High       | country_code must be in the approved country list.                               |            126 |      0.9753 | Standardise invalid country codes.                                |
| provider_feed    | PRV-001   | Uniqueness   | High       | provider_record_id must be unique.                                               |            114 |      0.9704 | Investigate duplicated records from third-party provider feeds.   |
| entities         | ENT-009   | Completeness | Medium     | private companies should have a registration number where available.             |            110 |      0.9784 | Improve enrichment for private company registration numbers.      |

## Critical Issues

| table_name       | rule_id   | dimension             | description                                                                      |   failed_count | recommendation                                                      |
|:-----------------|:----------|:----------------------|:---------------------------------------------------------------------------------|---------------:|:--------------------------------------------------------------------|
| kyc_attributes   | KYC-003   | Timeliness            | High and Critical risk counterparties should have been reviewed within 365 days. |           1209 | Prioritise stale high-risk counterparties for review.               |
| entities         | ENT-002   | Uniqueness            | entity_id must be unique.                                                        |            200 | Investigate duplicate entity IDs and apply survivorship rules.      |
| kyc_attributes   | KYC-001   | Referential Integrity | KYC entity_id must exist in entity master.                                       |             64 | Resolve orphan KYC records or create missing master entity records. |
| issuers          | ISS-002   | Uniqueness            | issuer_id must be unique.                                                        |             30 | Investigate duplicate issuer records.                               |
| issuers          | ISS-003   | Referential Integrity | issuer entity_id must exist in the entity master table.                          |             26 | Fix orphan issuer records by matching them to valid entity IDs.     |
| entity_hierarchy | HIER-001  | Referential Integrity | child_entity_id must exist in entity master.                                     |             26 | Resolve orphan child entities before publishing hierarchy data.     |
| entity_hierarchy | HIER-002  | Referential Integrity | parent_entity_id must exist in entity master.                                    |             23 | Resolve orphan parent entities before publishing hierarchy data.    |

## Recommended Remediation Actions

1. Prioritise critical referential integrity failures in issuer, hierarchy and KYC datasets.
2. Investigate duplicate master entity and issuer identifiers using survivorship rules.
3. Review stale active entity records and overdue high-risk KYC reviews.
4. Standardise provider country codes, entity types, statuses and confidence scores.
5. Move recurring checks into an automated scheduled workflow and publish quality scorecards regularly.

## Stakeholder Interpretation

This framework treats data quality as an operational and product discipline, not just a one-off validation exercise. The scorecards show which datasets are reliable, which rules are failing, and which remediation actions should be prioritised.

The output can support conversations between Product, Engineering, Data, Operations and Risk teams by creating a shared view of data quality, ownership and improvement priorities.