select distinct
    complaint_type,
    complaint_subtype
from {{ ref('stg_nyc_311_complaints') }}