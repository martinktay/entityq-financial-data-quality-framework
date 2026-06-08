-- EntityQ Executable SQL Quality Checks
-- Dataset: counterparty_trade_links
-- Purpose:
-- These SQL checks validate a dirty trade-linked counterparty reference dataset.
-- Each rule returns the failed records for that rule.

-- RULE_ID: SQL_TRADE_001
-- SEVERITY: Critical
-- DIMENSION: Completeness
-- DESCRIPTION: Trade ID must not be missing.
-- RECOMMENDATION: Ensure every trade-linked record has a populated trade identifier.
select
    trade_id,
    counterparty_entity_id,
    issuer_id,
    source_system,
    provider_name
from counterparty_trade_links
where trade_id is null
   or trim(cast(trade_id as varchar)) = '';


-- RULE_ID: SQL_TRADE_002
-- SEVERITY: Critical
-- DIMENSION: Uniqueness
-- DESCRIPTION: Trade ID must be unique.
-- RECOMMENDATION: Investigate duplicate trade identifiers across source systems.
select
    trade_id,
    counterparty_entity_id,
    issuer_id,
    source_system,
    provider_name
from counterparty_trade_links
where trade_id in (
    select trade_id
    from counterparty_trade_links
    where trade_id is not null
      and trim(cast(trade_id as varchar)) <> ''
    group by trade_id
    having count(*) > 1
);


-- RULE_ID: SQL_CP_001
-- SEVERITY: High
-- DIMENSION: Completeness
-- DESCRIPTION: Counterparty entity ID must not be missing.
-- RECOMMENDATION: Map each trade to a valid counterparty entity master record.
select
    trade_id,
    counterparty_entity_id,
    counterparty_name,
    source_system,
    provider_name
from counterparty_trade_links
where counterparty_entity_id is null
   or trim(cast(counterparty_entity_id as varchar)) = '';


-- RULE_ID: SQL_CP_002
-- SEVERITY: Medium
-- DIMENSION: Completeness
-- DESCRIPTION: Counterparty name should be populated and meaningful.
-- RECOMMENDATION: Enrich weak counterparty names from trusted reference data sources.
select
    trade_id,
    counterparty_entity_id,
    counterparty_name,
    source_system
from counterparty_trade_links
where counterparty_name is null
   or trim(cast(counterparty_name as varchar)) = ''
   or counterparty_name = 'Unknown Counterparty';


-- RULE_ID: SQL_ISSUER_001
-- SEVERITY: High
-- DIMENSION: Referential Integrity
-- DESCRIPTION: Issuer ID should resolve to a known issuer reference record.
-- RECOMMENDATION: Investigate issuer records not found in the issuer master dataset.
select
    trade_id,
    issuer_id,
    issuer_name,
    instrument_type,
    source_system
from counterparty_trade_links
where issuer_id is null
   or trim(cast(issuer_id as varchar)) = ''
   or issuer_id like 'ISS-ORPHAN%';


-- RULE_ID: SQL_DATE_001
-- SEVERITY: High
-- DIMENSION: Validity
-- DESCRIPTION: Trade date must be a valid date.
-- RECOMMENDATION: Fix invalid trade date values before downstream processing.
select
    trade_id,
    trade_date,
    settlement_date,
    source_system
from counterparty_trade_links
where try_cast(trade_date as date) is null;


-- RULE_ID: SQL_DATE_002
-- SEVERITY: High
-- DIMENSION: Validity
-- DESCRIPTION: Settlement date should not be before trade date.
-- RECOMMENDATION: Review settlement-date calculation and source-system date mappings.
select
    trade_id,
    trade_date,
    settlement_date,
    source_system
from counterparty_trade_links
where try_cast(trade_date as date) is not null
  and try_cast(settlement_date as date) is not null
  and try_cast(settlement_date as date) < try_cast(trade_date as date);


-- RULE_ID: SQL_AMOUNT_001
-- SEVERITY: High
-- DIMENSION: Validity
-- DESCRIPTION: Notional amount must be numeric and greater than zero.
-- RECOMMENDATION: Correct missing, non-numeric, zero or negative notional values.
select
    trade_id,
    counterparty_entity_id,
    notional_amount,
    currency,
    source_system
from counterparty_trade_links
where try_cast(notional_amount as double) is null
   or try_cast(notional_amount as double) <= 0;


-- RULE_ID: SQL_REF_001
-- SEVERITY: High
-- DIMENSION: Validity
-- DESCRIPTION: Currency must be an approved ISO-style currency code.
-- RECOMMENDATION: Standardise currency codes before downstream risk and reporting use.
select
    trade_id,
    currency,
    notional_amount,
    source_system
from counterparty_trade_links
where currency not in ('USD', 'GBP', 'EUR', 'NGN', 'JPY', 'CHF', 'CAD', 'AUD')
   or currency is null
   or trim(cast(currency as varchar)) = '';


-- RULE_ID: SQL_REF_002
-- SEVERITY: High
-- DIMENSION: Validity
-- DESCRIPTION: Risk country must be a valid supported country code.
-- RECOMMENDATION: Map invalid risk-country values to controlled reference data.
select
    trade_id,
    counterparty_entity_id,
    risk_country,
    booking_country,
    source_system
from counterparty_trade_links
where risk_country not in (
    'US', 'GB', 'NG', 'DE', 'FR', 'CA', 'SG', 'AE', 'ZA', 'NL',
    'CH', 'IE', 'IN', 'BR', 'AU', 'JP', 'HK', 'LU'
)
or risk_country is null
or trim(cast(risk_country as varchar)) = '';


-- RULE_ID: SQL_REF_003
-- SEVERITY: Medium
-- DIMENSION: Validity
-- DESCRIPTION: Instrument type must be in the approved instrument taxonomy.
-- RECOMMENDATION: Standardise instrument classification values.
select
    trade_id,
    instrument_type,
    instrument_id,
    issuer_id
from counterparty_trade_links
where instrument_type not in (
    'Equity',
    'Bond',
    'Fund',
    'Private Credit',
    'Private Equity',
    'Derivative'
)
or instrument_type is null
or trim(cast(instrument_type as varchar)) = '';


-- RULE_ID: SQL_KYC_001
-- SEVERITY: Critical
-- DIMENSION: Compliance
-- DESCRIPTION: High-risk counterparties should have approved KYC.
-- RECOMMENDATION: Prioritise remediation of high-risk counterparties with incomplete KYC.
select
    trade_id,
    counterparty_entity_id,
    counterparty_name,
    kyc_status,
    counterparty_risk_rating,
    notional_amount,
    currency
from counterparty_trade_links
where counterparty_risk_rating = 'High'
  and kyc_status <> 'Approved';


-- RULE_ID: SQL_PROVIDER_001
-- SEVERITY: High
-- DIMENSION: Validity
-- DESCRIPTION: Provider confidence score must be between 0 and 1.
-- RECOMMENDATION: Review provider scoring feed and reject invalid scores.
select
    trade_id,
    provider_name,
    provider_confidence_score,
    source_system
from counterparty_trade_links
where try_cast(provider_confidence_score as double) is null
   or try_cast(provider_confidence_score as double) < 0
   or try_cast(provider_confidence_score as double) > 1;


-- RULE_ID: SQL_PROVIDER_002
-- SEVERITY: Medium
-- DIMENSION: Accuracy
-- DESCRIPTION: Provider confidence score should not be below 0.70.
-- RECOMMENDATION: Route low-confidence provider records for review or enrichment.
select
    trade_id,
    provider_name,
    provider_confidence_score,
    source_system
from counterparty_trade_links
where try_cast(provider_confidence_score as double) is not null
  and try_cast(provider_confidence_score as double) >= 0
  and try_cast(provider_confidence_score as double) < 0.70;


-- RULE_ID: SQL_SECURITY_001
-- SEVERITY: Medium
-- DIMENSION: Validity
-- DESCRIPTION: ISIN should follow a 12-character security identifier pattern.
-- RECOMMENDATION: Validate security identifiers against trusted instrument reference data.
select
    trade_id,
    issuer_id,
    isin,
    instrument_type
from counterparty_trade_links
where regexp_matches(cast(isin as varchar), '^[A-Z]{2}[A-Z0-9]{10}$') = false
   or isin is null
   or trim(cast(isin as varchar)) = '';


-- RULE_ID: SQL_ENTITY_001
-- SEVERITY: Medium
-- DIMENSION: Validity
-- DESCRIPTION: LEI should follow a 20-character alphanumeric pattern.
-- RECOMMENDATION: Enrich or correct invalid legal entity identifiers.
select
    trade_id,
    counterparty_entity_id,
    lei,
    counterparty_name
from counterparty_trade_links
where regexp_matches(cast(lei as varchar), '^[A-Z0-9]{20}$') = false
   or lei is null
   or trim(cast(lei as varchar)) = '';


-- RULE_ID: SQL_TIME_001
-- SEVERITY: Medium
-- DIMENSION: Timeliness
-- DESCRIPTION: Reference data should be verified within the last 365 days.
-- RECOMMENDATION: Refresh stale counterparty and issuer reference records.
select
    trade_id,
    counterparty_entity_id,
    last_verified_date,
    source_system
from counterparty_trade_links
where try_cast(last_verified_date as date) is not null
  and try_cast(last_verified_date as date) < current_date - interval '365 days';


-- RULE_ID: SQL_REVIEW_001
-- SEVERITY: High
-- DIMENSION: Risk Review
-- DESCRIPTION: Large trades involving high-risk or incomplete-KYC counterparties require review.
-- RECOMMENDATION: Route large high-risk or incomplete-KYC trades to compliance and risk review.
select
    trade_id,
    counterparty_entity_id,
    counterparty_name,
    notional_amount,
    currency,
    kyc_status,
    counterparty_risk_rating
from counterparty_trade_links
where try_cast(notional_amount as double) >= 10000000
  and (
      counterparty_risk_rating = 'High'
      or kyc_status <> 'Approved'
  );