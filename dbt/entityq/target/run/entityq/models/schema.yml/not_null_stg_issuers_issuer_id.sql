
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select issuer_id
from "entityq"."main"."stg_issuers"
where issuer_id is null



  
  
      
    ) dbt_internal_test