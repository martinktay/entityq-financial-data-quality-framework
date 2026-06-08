
  
  create view "entityq"."main"."stg_entity_hierarchy__dbt_tmp" as (
    with source as (

    select *
    from read_csv_auto('../../data/raw/entity_hierarchy.csv', header = true)

),

renamed as (

    select
        cast(child_entity_id as varchar) as child_entity_id,
        cast(parent_entity_id as varchar) as parent_entity_id,
        cast(relationship_type as varchar) as relationship_type,
        try_cast(ownership_percentage as double) as ownership_percentage,
        try_cast(effective_from as date) as effective_from,
        try_cast(effective_to as date) as effective_to,
        cast(source_system as varchar) as source_system
    from source

)

select * from renamed
  );
