with source as (

    select *
    from read_csv_auto('../../data/raw/provider_feed.csv', header = true)

),

renamed as (

    select
        cast(provider_record_id as varchar) as provider_record_id,
        cast(provider_name as varchar) as provider_name,
        cast(legal_name as varchar) as legal_name,
        cast(country_code as varchar) as country_code,
        cast(registration_number as varchar) as registration_number,
        cast(sector as varchar) as sector,
        cast(status as varchar) as status,
        try_cast(confidence_score as double) as confidence_score,
        try_cast(feed_date as date) as feed_date
    from source

)

select * from renamed