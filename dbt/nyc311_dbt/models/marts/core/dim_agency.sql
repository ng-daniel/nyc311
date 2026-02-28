select distinct
    agency,
    agency_name
from {{ ref('stg_nyc_311_complaints') }}