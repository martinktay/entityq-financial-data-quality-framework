# EntityQ Quality Rules Catalog

This document lists the main data quality rules used in the EntityQ framework.

## Entity Master Rules

| Rule ID | Dimension | Severity | Rule |
|---|---|---|---|
| ENT-001 | Completeness | Critical | `entity_id` must not be null |
| ENT-002 | Uniqueness | Critical | `entity_id` must be unique |
| ENT-003 | Completeness | High | `legal_name` must not be null |
| ENT-004 | Validity | High | `country_code` must be in the approved country list |
| ENT-005 | Validity | Medium | `entity_type` must be in the approved taxonomy |
| ENT-006 | Validity | Medium | `status` must be in the approved status list |
| ENT-007 | Validity | High | `incorporation_date` cannot be in the future |
| ENT-008 | Timeliness | Medium | Active entities should be verified within the last 365 days |
| ENT-009 | Completeness | Medium | Private companies should have registration numbers where available |

## Issuer Rules

| Rule ID | Dimension | Severity | Rule |
|---|---|---|---|
| ISS-001 | Completeness | Critical | `issuer_id` must not be null |
| ISS-002 | Uniqueness | Critical | `issuer_id` must be unique |
| ISS-003 | Referential Integrity | Critical | Issuer `entity_id` must exist in entity master |
| ISS-004 | Validity | Medium | `instrument_type` must be in the approved instrument list |
| ISS-005 | Completeness | High | Listed issuers should have an exchange code |

## Hierarchy Rules

| Rule ID | Dimension | Severity | Rule |
|---|---|---|---|
| HIER-001 | Referential Integrity | Critical | `child_entity_id` must exist in entity master |
| HIER-002 | Referential Integrity | Critical | `parent_entity_id` must exist in entity master |
| HIER-003 | Validity | High | `child_entity_id` cannot equal `parent_entity_id` |
| HIER-004 | Validity | High | `ownership_percentage` must be between 0 and 100 |
| HIER-005 | Hierarchy Integrity | High | Hierarchy should not contain circular parent-child relationships |

## KYC Rules

| Rule ID | Dimension | Severity | Rule |
|---|---|---|---|
| KYC-001 | Referential Integrity | Critical | KYC `entity_id` must exist in entity master |
| KYC-002 | Validity | High | `risk_rating` must be Low, Medium, High or Critical |
| KYC-003 | Timeliness | Critical | High and Critical risk counterparties should be reviewed within 365 days |
| KYC-004 | Timeliness | High | `next_review_due_date` should not be overdue |

## Provider Feed Rules

| Rule ID | Dimension | Severity | Rule |
|---|---|---|---|
| PRV-001 | Uniqueness | High | `provider_record_id` must be unique |
| PRV-002 | Completeness | High | Provider `legal_name` must not be null |
| PRV-003 | Validity | Medium | `confidence_score` must be between 0 and 1 |
| PRV-004 | Consistency | Medium | Provider `registration_number` should match internal master where available |

## Rule Design Notes

Each rule produces:

- table name
- rule ID
- quality dimension
- severity
- description
- total records checked
- failed record count
- passed record count
- pass rate
- recommendation
- examples of failed records

This makes the output useful for both technical debugging and stakeholder reporting.