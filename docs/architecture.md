# EntityQ Architecture

## Overview

EntityQ is designed as a modular data quality and automation framework.

The core pipeline has six stages:

1. Data generation
2. Data profiling
3. Rule-based validation
4. Quality metrics
5. Anomaly detection
6. Stakeholder reporting

## Architecture Flow

```text
Synthetic raw data generation
        ↓
Raw CSV datasets
        ↓
Data profiling
        ↓
Validation rules
        ↓
Quality scorecards
        ↓
AI/ML anomaly detection
        ↓
Stakeholder report