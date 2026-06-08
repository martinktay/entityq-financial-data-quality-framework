
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select entity_id
from "entityq"."main"."stg_kyc_attributes"
where entity_id is null



  
  
      
    ) dbt_internal_test