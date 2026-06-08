# EntityQ Trino Lab

## Purpose

This lab documents the local Trino setup for EntityQ.

Trino is used to demonstrate familiarity with distributed SQL access patterns for curated entity, issuer, KYC, provider feed and data quality tables.

## Local Setup

Trino was run locally using Docker:

```bash
docker run --name entityq-trino -d -p 8081:8080 trinodb/trino