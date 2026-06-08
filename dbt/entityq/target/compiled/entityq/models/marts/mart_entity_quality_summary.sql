with entities as (

    select * from "entityq"."main"."stg_entities"

),

summary as (

    select
        source_system,
        count(*) as total_records,

        sum(
            case
                when legal_name is null
                then 1 else 0
            end
        ) as missing_legal_name_count,

        sum(
            case
                when registration_number is null
                then 1 else 0
            end
        ) as missing_registration_number_count,

        sum(
            case
                when country_code not in (
                    'US', 'GB', 'NG', 'DE', 'FR', 'CA', 'SG', 'AE', 'ZA', 'NL',
                    'CH', 'IE', 'IN', 'BR', 'AU', 'JP', 'HK', 'LU'
                )
                or country_code is null
                then 1 else 0
            end
        ) as invalid_country_count,

        sum(
            case
                when status = 'Active'
                 and last_verified_date < current_date - interval '365 days'
                then 1 else 0
            end
        ) as stale_active_record_count

    from entities
    group by source_system

)

select * from summary