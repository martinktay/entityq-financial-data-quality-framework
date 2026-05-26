CREATE TABLE IF NOT EXISTS entities (
    entity_id VARCHAR,
    legal_name VARCHAR,
    normalized_name VARCHAR,
    country_code VARCHAR,
    registration_number VARCHAR,
    entity_type VARCHAR,
    sector VARCHAR,
    industry VARCHAR,
    status VARCHAR,
    incorporation_date DATE,
    last_verified_date DATE,
    source_system VARCHAR,
    created_at DATE,
    updated_at DATE
);


CREATE TABLE IF NOT EXISTS issuers (
    issuer_id VARCHAR,
    entity_id VARCHAR,
    issuer_name VARCHAR,
    instrument_type VARCHAR,
    market VARCHAR,
    listing_status VARCHAR,
    exchange_code VARCHAR,
    risk_country VARCHAR,
    source_system VARCHAR
);

CREATE TABLE IF NOT EXISTS entity_hierarchy (
    child_entity_id VARCHAR,
    parent_entity_id VARCHAR,
    relationship_type VARCHAR,
    ownership_percentage DOUBLE,
    effective_from DATE,
    effective_to DATE,
    source_system VARCHAR
);

CREATE TABLE IF NOT EXISTS kyc_attributes (
    entity_id VARCHAR,
    kyc_status VARCHAR,
    risk_rating VARCHAR,
    sanctions_flag VARCHAR,
    pep_flag VARCHAR,
    counterparty_type VARCHAR,
    last_review_date DATE,
    next_review_due_date DATE,
    source_system VARCHAR
);

CREATE TABLE IF NOT EXISTS provider_feed (
    provider_record_id VARCHAR,
    provider_name VARCHAR,
    legal_name VARCHAR,
    country_code VARCHAR,
    registration_number VARCHAR,
    sector VARCHAR,
    status VARCHAR,
    confidence_score DOUBLE,
    feed_date DATE
);