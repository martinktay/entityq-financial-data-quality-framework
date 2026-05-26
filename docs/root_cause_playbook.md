# EntityQ Root-Cause Playbook

## Purpose

This playbook explains how common data quality issues should be investigated and remediated.

A strong data quality framework should not only detect issues. It should also support root-cause analysis, prioritisation and remediation.

## 1. Duplicate Entity IDs

### Possible Causes

- repeated ingestion from a provider feed
- incorrect merge logic
- missing survivorship rules
- manual upload error
- broken entity resolution process

### Investigation Steps

1. Check the source systems for duplicate records.
2. Compare legal name, country code and registration number.
3. Review whether records represent the same legal entity.
4. Identify which source should be the golden record.
5. Apply survivorship rules.

### Remediation

- create or improve entity matching rules
- define golden record selection logic
- reject duplicate identifiers during ingestion
- monitor duplicate rate by source system

## 2. Missing Legal Names

### Possible Causes

- incomplete provider feed
- manual data entry issue
- ingestion mapping error
- missing mandatory field validation

### Investigation Steps

1. Identify the source system.
2. Check whether the legal name exists in the upstream feed.
3. Review ingestion mappings.
4. Confirm whether the entity should be active.

### Remediation

- make legal name mandatory for active records
- reject records with missing legal names
- request provider enrichment
- add completeness monitoring

## 3. Invalid Country Codes

### Possible Causes

- provider taxonomy mismatch
- free-text country values
- empty or unknown country values
- incorrect mapping table

### Investigation Steps

1. Identify invalid values.
2. Compare values against approved country list.
3. Review source-specific mapping logic.
4. Check whether invalid codes are concentrated in one provider.

### Remediation

- maintain approved country code reference table
- add country code validation at ingestion
- create source-specific standardisation logic
- monitor invalid country counts by source

## 4. Orphan Issuer Records

### Possible Causes

- issuer feed arrived before entity master update
- incorrect entity ID mapping
- deleted or merged entity records
- provider supplied unknown entity reference

### Investigation Steps

1. Identify issuer records with no matching entity.
2. Match issuer name against legal entity names.
3. Compare registration numbers where available.
4. Review provider mapping logic.

### Remediation

- enrich missing entity master records
- fix issuer-to-entity mapping
- reject issuer records without valid master linkage
- add referential integrity checks to the pipeline

## 5. Hierarchy Exceptions

### Possible Causes

- incorrect parent-child mapping
- self-referencing hierarchy record
- circular ownership relationship
- invalid ownership percentage

### Investigation Steps

1. Check whether child equals parent.
2. Identify missing parent or child entities.
3. Review ownership percentage values.
4. Detect circular relationships.

### Remediation

- remove self-referencing records
- correct invalid ownership values
- improve corporate hierarchy rules
- add hierarchy survivorship logic

## 6. Stale KYC Reviews

### Possible Causes

- delayed risk review process
- missing review workflow
- stale KYC system export
- high-risk entities not prioritised

### Investigation Steps

1. Identify High and Critical risk entities.
2. Compare last review date against policy.
3. Check next review due date.
4. Prioritise overdue high-risk records.

### Remediation

- create remediation queue for high-risk entities
- monitor overdue KYC rates
- add alerts for upcoming review due dates
- improve KYC workflow ownership

## 7. Invalid Provider Confidence Scores

### Possible Causes

- provider data contract issue
- scoring system change
- ingestion type casting issue
- missing validation at source

### Investigation Steps

1. Identify provider records with confidence below 0 or above 1.
2. Check whether values are concentrated in one provider.
3. Review recent provider feed changes.
4. Confirm expected score format.

### Remediation

- reject invalid confidence scores
- agree provider data quality standards
- add provider-level monitoring
- document score range expectations

## Remediation Ownership Model

Each issue should have:

- rule ID
- severity
- affected table
- source system
- owner
- recommended action
- expected resolution date
- current status

## Prioritisation Model

Issues should be prioritised in this order:

1. Critical referential integrity failures
2. High-risk KYC and counterparty risk issues
3. Duplicate master identifiers
4. Invalid legal or country identifiers
5. Missing optional enrichment fields
6. Low-impact provider format issues