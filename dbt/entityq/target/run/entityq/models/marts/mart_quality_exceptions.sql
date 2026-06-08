
  
    
    

    create  table
      "entityq"."main"."mart_quality_exceptions__dbt_tmp"
  
    as (
      with entities as (

    select * from "entityq"."main"."stg_entities"

),

issuers as (

    select * from "entityq"."main"."stg_issuers"

),

kyc as (

    select * from "entityq"."main"."stg_kyc_attributes"

),

entity_exceptions as (

    select
        'entities' as table_name,
        entity_id as record_id,
        'Missing legal name' as issue_type,
        'High' as severity,
        source_system
    from entities
    where legal_name is null

    union all

    select
        'entities' as table_name,
        entity_id as record_id,
        'Invalid country code' as issue_type,
        'High' as severity,
        source_system
    from entities
    where country_code not in (
        'US', 'GB', 'NG', 'DE', 'FR', 'CA', 'SG', 'AE', 'ZA', 'NL',
        'CH', 'IE', 'IN', 'BR', 'AU', 'JP', 'HK', 'LU'
    )
    or country_code is null

),

issuer_exceptions as (

    select
        'issuers' as table_name,
        issuers.issuer_id as record_id,
        'Issuer entity_id not found in entity master' as issue_type,
        'Critical' as severity,
        issuers.source_system
    from issuers
    left join entities
        on issuers.entity_id = entities.entity_id
    where entities.entity_id is null

),

kyc_exceptions as (

    select
        'kyc_attributes' as table_name,
        entity_id as record_id,
        'Overdue KYC review' as issue_type,
        'High' as severity,
        source_system
    from kyc
    where next_review_due_date < current_date

)

select * from entity_exceptions

union all

select * from issuer_exceptions

union all

select * from kyc_exceptions
    );
  
  