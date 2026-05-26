-- EntityQ SQL Quality Checks
-- These queries express key data quality rules using SQL.

-- 1. Duplicate entity IDs
SELECT
    entity_id,
    COUNT(*) AS record_count
FROM entities
GROUP BY entity_id
HAVING COUNT(*) > 1;


-- 2. Missing legal names
SELECT
    COUNT(*) AS missing_legal_name_count
FROM entities
WHERE legal_name IS NULL;


-- 3. Invalid country codes
SELECT
    entity_id,
    legal_name,
    country_code,
    source_system
FROM entities
WHERE country_code NOT IN (
    'US', 'GB', 'NG', 'DE', 'FR', 'CA', 'SG', 'AE', 'ZA', 'NL',
    'CH', 'IE', 'IN', 'BR', 'AU', 'JP', 'HK', 'LU'
)
OR country_code IS NULL;


-- 4. Invalid entity types
SELECT
    entity_id,
    legal_name,
    entity_type
FROM entities
WHERE entity_type NOT IN (
    'Public Company',
    'Private Company',
    'Fund',
    'SPV',
    'Government Entity',
    'Financial Institution'
)
OR entity_type IS NULL;


-- 5. Stale active entity records
SELECT
    entity_id,
    legal_name,
    status,
    last_verified_date
FROM entities
WHERE status = 'Active'
  AND last_verified_date < CURRENT_DATE - INTERVAL '365 days';


-- 6. Orphan issuer records
SELECT
    i.issuer_id,
    i.entity_id,
    i.issuer_name,
    i.source_system
FROM issuers i
LEFT JOIN entities e
    ON i.entity_id = e.entity_id
WHERE e.entity_id IS NULL;


-- 7. Listed issuers missing exchange code
SELECT
    issuer_id,
    entity_id,
    issuer_name,
    listing_status,
    exchange_code
FROM issuers
WHERE listing_status = 'Listed'
  AND exchange_code IS NULL;


-- 8. Orphan child entities in hierarchy
SELECT
    h.child_entity_id,
    h.parent_entity_id,
    h.relationship_type,
    h.source_system
FROM entity_hierarchy h
LEFT JOIN entities e
    ON h.child_entity_id = e.entity_id
WHERE e.entity_id IS NULL;


-- 9. Orphan parent entities in hierarchy
SELECT
    h.child_entity_id,
    h.parent_entity_id,
    h.relationship_type,
    h.source_system
FROM entity_hierarchy h
LEFT JOIN entities e
    ON h.parent_entity_id = e.entity_id
WHERE e.entity_id IS NULL;


-- 10. Self-referencing hierarchy relationships
SELECT
    child_entity_id,
    parent_entity_id,
    relationship_type
FROM entity_hierarchy
WHERE child_entity_id = parent_entity_id;


-- 11. Invalid ownership percentages
SELECT
    child_entity_id,
    parent_entity_id,
    ownership_percentage
FROM entity_hierarchy
WHERE ownership_percentage < 0
   OR ownership_percentage > 100
   OR ownership_percentage IS NULL;


-- 12. Orphan KYC records
SELECT
    k.entity_id,
    k.kyc_status,
    k.risk_rating,
    k.source_system
FROM kyc_attributes k
LEFT JOIN entities e
    ON k.entity_id = e.entity_id
WHERE e.entity_id IS NULL;


-- 13. Invalid risk ratings
SELECT
    entity_id,
    risk_rating,
    source_system
FROM kyc_attributes
WHERE risk_rating NOT IN ('Low', 'Medium', 'High', 'Critical')
   OR risk_rating IS NULL;


-- 14. Overdue KYC reviews
SELECT
    entity_id,
    risk_rating,
    next_review_due_date
FROM kyc_attributes
WHERE next_review_due_date < CURRENT_DATE;


-- 15. High-risk counterparties with stale reviews
SELECT
    entity_id,
    risk_rating,
    last_review_date
FROM kyc_attributes
WHERE risk_rating IN ('High', 'Critical')
  AND last_review_date < CURRENT_DATE - INTERVAL '365 days';


-- 16. Duplicate provider records
SELECT
    provider_record_id,
    COUNT(*) AS record_count
FROM provider_feed
GROUP BY provider_record_id
HAVING COUNT(*) > 1;


-- 17. Provider records missing legal names
SELECT
    provider_record_id,
    provider_name,
    legal_name
FROM provider_feed
WHERE legal_name IS NULL;


-- 18. Invalid provider confidence scores
SELECT
    provider_record_id,
    provider_name,
    confidence_score
FROM provider_feed
WHERE confidence_score < 0
   OR confidence_score > 1
   OR confidence_score IS NULL;