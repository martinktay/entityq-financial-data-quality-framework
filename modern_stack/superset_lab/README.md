# EntityQ Superset Lab

## Purpose

This lab documents the local Superset setup used to explore how EntityQ data quality outputs could be visualised in a BI and reporting layer.

Superset is used here as the dashboarding layer for quality scorecards, failed rules, provider feed issues, KYC exceptions, issuer linkage issues, and anomaly review workflows.

## Local Setup

Superset was run locally using Docker.

The direct container approach was used because the cloned Superset Docker Compose development setup attempted to build Superset from source and introduced dependency and image-resolution issues that were unnecessary for this project.

## Docker Run Command

```bash
docker run -d --name entityq-superset -p 8088:8088 -v entityq_superset_home:/app/superset_home -e SUPERSET_SECRET_KEY="entityq-local-dev-secret-key-change-me" apache/superset:latest
```

## Superset Initialisation

After starting the container, Superset was initialised with:

```bash
docker exec -it entityq-superset superset db upgrade

docker exec -it entityq-superset superset fab create-admin --username admin --firstname Superset --lastname Admin --email admin@superset.com --password admin

docker exec -it entityq-superset superset init

docker restart entityq-superset
```

## Local URL

```text
http://localhost:8088
```

## Login

```text
Username: admin
Password: admin
```

## EntityQ Dashboard Use Cases

In a production-style EntityQ architecture, Superset could be used to build dashboards for:

* entity quality scorecards
* failed validation rules
* rule failures by severity
* provider feed quality issues
* Kafka provider feed event failures
* overdue KYC reviews
* issuer records not linked to entity master data
* corporate hierarchy integrity issues
* anomaly candidates requiring analyst review

## Example Dashboard Pages

### 1. Executive Data Quality Overview

Purpose:

Show senior stakeholders the overall health of entity and reference data.

Possible metrics:

* total records processed
* total failed rules
* average quality score
* critical issue count
* records requiring remediation

### 2. Provider Feed Quality Monitoring

Purpose:

Track third-party provider feed quality.

Possible metrics:

* provider events processed
* passed versus failed provider events
* invalid country code count
* missing legal name count
* invalid confidence score count

### 3. KYC and Counterparty Risk Exceptions

Purpose:

Monitor KYC and risk-related data quality issues.

Possible metrics:

* overdue KYC review count
* high-risk counterparty count
* sanctions flag count
* PEP flag count
* missing counterparty type count

### 4. Issuer and Corporate Hierarchy Integrity

Purpose:

Identify relationship and linkage issues across issuer and entity hierarchy datasets.

Possible metrics:

* orphan issuer count
* invalid parent-child relationship count
* invalid ownership percentage count
* missing hierarchy records

### 5. Anomaly Review Dashboard

Purpose:

Support analysts reviewing unusual entity records identified through AI/ML-enabled quality checks.

Possible metrics:

* anomaly candidate count
* anomaly candidates by source system
* anomaly candidates by country
* anomaly candidates by entity type

## Role Alignment

This lab demonstrates familiarity with using Superset as a stakeholder reporting layer for data quality monitoring.

It supports the EntityQ architecture by showing how data quality metrics, failed rules, provider feed issues and anomaly outputs can be made accessible to Product, Engineering, Data and business stakeholders through dashboards.
