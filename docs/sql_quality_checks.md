# EntityQ SQL Quality Checks

## Purpose

This document explains the executable SQL quality checks in EntityQ.

The SQL layer demonstrates how a newly onboarded dirty financial dataset can be validated using transparent SQL rules. This is important because many data quality workflows in financial organisations rely on SQL-based profiling, exception detection, reconciliation and reporting.

## Dataset

The SQL checks run against:

```text
data/incoming/counterparty_trade_links.csv