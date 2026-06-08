# EntityQ Apache Iceberg Lab

## Purpose

This lab documents local Apache Iceberg exploration for EntityQ.

Iceberg is used here to demonstrate familiarity with curated table architecture for scalable analytical datasets. In a production-style EntityQ workflow, validated entity, issuer, KYC, hierarchy, provider feed and quality exception datasets could be stored in Iceberg-style curated tables.

## Local Setup

This lab uses Docker Compose with:

- Spark with Iceberg support
- Iceberg REST Catalog
- MinIO object storage
- MinIO client

## Start the Lab

From this folder:

```bash
docker compose up -d