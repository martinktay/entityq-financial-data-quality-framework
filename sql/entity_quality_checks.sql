-- EntityQ SQL Quality Checks
-- Purpose:
-- These checks show how SQL can be used to validate entity, issuer,
-- hierarchy, KYC and provider feed datasets.

-- 1. Duplicate entity identifiers
select
    entity_id,
    count(*) as duplicate_count
from entities
group by entity_id
having count(*) > 1;


-- 2. Missing legal names
select
    entity_id,
    source_system,
    country_code,
    registration_number
from entities
where legal_name is null
   or trim(legal_name) = '';


-- 3. Invalid country codes
select
    entity_id,
    legal_name,
    country_code,
    source_system
from entities
where country_code not in (
    'US', 'GB', 'NG', 'DE', 'FR', 'CA', 'SG', 'AE', 'ZA', 'NL',
    'CH', 'IE', 'IN', 'BR', 'AU', 'JP', 'HK', 'LU'
)
or country_code is null;


-- 4. Stale active entity records
select
    entity_id,
    legal_name,
    status,
    last_verified_date,
    source_system
from entities
where status = 'Active'
  and last_verified_date < current_date - interval '365 days';


-- 5. Issuer records not linked to entity master
select
    issuers.issuer_id,
    issuers.entity_id,
    issuers.issuer_name,
    issuers.market,
    issuers.risk_country
from issuers
left join entities
    on issuers.entity_id = entities.entity_id
where entities.entity_id is null;


-- 6. Invalid corporate hierarchy relationships
select
    child_entity_id,
    parent_entity_id,
    relationship_type,
    ownership_percentage
from entity_hierarchy
where child_entity_id = parent_entity_id
   or ownership_percentage < 0
   or ownership_percentage > 100;


-- 7. Overdue KYC reviews
select
    kyc.entity_id,
    entities.legal_name,
    kyc.kyc_status,
    kyc.risk_rating,
    kyc.next_review_due_date
from kyc_attributes kyc
left join entities
    on kyc.entity_id = entities.entity_id
where kyc.next_review_due_date < current_date;


-- 8. Low-confidence provider records
select
    provider_record_id,
    provider_name,
    legal_name,
    country_code,
    confidence_score,
    feed_date
from provider_feed
where confidence_score < 0.70
   or confidence_score is null;