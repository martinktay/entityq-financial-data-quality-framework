with source as (

    select *
    from read_csv_auto('../../data/raw/kyc_attributes.csv', header = true)

),

renamed as (

    select
        cast(entity_id as varchar) as entity_id,
        cast(kyc_status as varchar) as kyc_status,
        cast(risk_rating as varchar) as risk_rating,
        cast(sanctions_flag as varchar) as sanctions_flag,
        cast(pep_flag as varchar) as pep_flag,
        cast(counterparty_type as varchar) as counterparty_type,
        try_cast(last_review_date as date) as last_review_date,
        try_cast(next_review_due_date as date) as next_review_due_date,
        cast(source_system as varchar) as source_system
    from source

)

select * from renamed