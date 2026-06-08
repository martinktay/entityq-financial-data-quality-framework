with source as (

    select *
    from read_csv_auto('../../data/raw/entities.csv', header = true)

),

renamed as (

    select
        cast(entity_id as varchar) as entity_id,
        cast(legal_name as varchar) as legal_name,
        cast(normalized_name as varchar) as normalized_name,
        cast(country_code as varchar) as country_code,
        cast(registration_number as varchar) as registration_number,
        cast(entity_type as varchar) as entity_type,
        cast(sector as varchar) as sector,
        cast(industry as varchar) as industry,
        cast(status as varchar) as status,
        try_cast(incorporation_date as date) as incorporation_date,
        try_cast(last_verified_date as date) as last_verified_date,
        cast(source_system as varchar) as source_system,
        try_cast(created_at as date) as created_at,
        try_cast(updated_at as date) as updated_at
    from source

)

select * from renamed