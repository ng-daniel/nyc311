select
    created_date,
    latitude_rounded,
    longitude_rounded,

    count(*) as complaint_count,
    avg(resolution_hours) as avg_resolution_hours

from {{ ref('fct_311_complaints') }}

where
    has_location_data

group by 1,2,3