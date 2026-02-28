select
    agency,
    date_trunc('month', created_at) as month,

    count(*) as complaint_count,
    avg(resolution_hours) as avg_resolution_hours

from {{ ref('fct_311_complaints') }}

group by 1,2