
  
  create view "entityq"."main"."stg_issuers__dbt_tmp" as (
    with source as (

    select *
    from read_csv_auto('../../data/raw/issuers.csv', header = true)

),

renamed as (

    select
        cast(issuer_id as varchar) as issuer_id,
        cast(entity_id as varchar) as entity_id,
        cast(issuer_name as varchar) as issuer_name,
        cast(instrument_type as varchar) as instrument_type,
        cast(market as varchar) as market,
        cast(listing_status as varchar) as listing_status,
        cast(exchange_code as varchar) as exchange_code,
        cast(risk_country as varchar) as risk_country,
        cast(source_system as varchar) as source_system
    from source

)

select * from renamed
  );
