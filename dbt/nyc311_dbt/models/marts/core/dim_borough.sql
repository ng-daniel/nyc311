select distinct
    borough
from {{ ref('stg_nyc_311_complaints') }}
where borough is not null