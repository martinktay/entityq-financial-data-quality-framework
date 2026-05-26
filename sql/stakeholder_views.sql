-- EntityQ Stakeholder Views
-- These views are examples of how quality results can be exposed to analysts,
-- product managers, data teams and operational stakeholders.

-- View 1: Entity quality issue summary by source system
CREATE OR REPLACE VIEW vw_entity_quality_by_source AS
SELECT
    source_system,
    COUNT(*) AS total_records,
    SUM(CASE WHEN legal_name IS NULL THEN 1 ELSE 0 END) AS missing_legal_name_count,
    SUM(CASE WHEN registration_number IS NULL THEN 1 ELSE 0 END) AS missing_registration_count,
    SUM(
        CASE
            WHEN country_code NOT IN (
                'US', 'GB', 'NG', 'DE', 'FR', 'CA', 'SG', 'AE', 'ZA', 'NL',
                'CH', 'IE', 'IN', 'BR', 'AU', 'JP', 'HK', 'LU'
            )
            OR country_code IS NULL
            THEN 1 ELSE 0
        END
    ) AS invalid_country_count,
    SUM(
        CASE
            WHEN status = 'Active'
             AND last_verified_date < CURRENT_DATE - INTERVAL '365 days'
            THEN 1 ELSE 0
        END
    ) AS stale_active_record_count
FROM entities
GROUP BY source_system;


-- View 2: KYC review risk summary
CREATE OR REPLACE VIEW vw_kyc_review_risk_summary AS
SELECT
    risk_rating,
    COUNT(*) AS total_records,
    SUM(
        CASE
            WHEN next_review_due_date < CURRENT_DATE
            THEN 1 ELSE 0
        END
    ) AS overdue_review_count,
    SUM(
        CASE
            WHEN risk_rating IN ('High', 'Critical')
             AND last_review_date < CURRENT_DATE - INTERVAL '365 days'
            THEN 1 ELSE 0
        END
    ) AS stale_high_risk_review_count
FROM kyc_attributes
GROUP BY risk_rating;


-- View 3: Issuer linkage summary
CREATE OR REPLACE VIEW vw_issuer_linkage_summary AS
SELECT
    i.source_system,
    COUNT(*) AS total_issuer_records,
    SUM(
        CASE
            WHEN e.entity_id IS NULL
            THEN 1 ELSE 0
        END
    ) AS orphan_issuer_count,
    SUM(
        CASE
            WHEN i.listing_status = 'Listed'
             AND i.exchange_code IS NULL
            THEN 1 ELSE 0
        END
    ) AS listed_missing_exchange_count
FROM issuers i
LEFT JOIN entities e
    ON i.entity_id = e.entity_id
GROUP BY i.source_system;


-- View 4: Hierarchy exception summary
CREATE OR REPLACE VIEW vw_hierarchy_exception_summary AS
SELECT
    source_system,
    COUNT(*) AS total_relationships,
    SUM(
        CASE
            WHEN child_entity_id = parent_entity_id
            THEN 1 ELSE 0
        END
    ) AS self_reference_count,
    SUM(
        CASE
            WHEN ownership_percentage < 0
              OR ownership_percentage > 100
              OR ownership_percentage IS NULL
            THEN 1 ELSE 0
        END
    ) AS invalid_ownership_count
FROM entity_hierarchy
GROUP BY source_system;


-- View 5: Provider feed quality summary
CREATE OR REPLACE VIEW vw_provider_feed_quality_summary AS
SELECT
    provider_name,
    COUNT(*) AS total_provider_records,
    SUM(
        CASE
            WHEN legal_name IS NULL
            THEN 1 ELSE 0
        END
    ) AS missing_legal_name_count,
    SUM(
        CASE
            WHEN confidence_score < 0
              OR confidence_score > 1
              OR confidence_score IS NULL
            THEN 1 ELSE 0
        END
    ) AS invalid_confidence_score_count
FROM provider_feed
GROUP BY provider_name;