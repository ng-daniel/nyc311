select
    complaint_id,
    created_at,
    closed_at,
    created_date,

    borough,
    agency,
    complaint_type,
    status,

    resolution_hours,
    resolution_bucket,

    latitude,
    longitude

from {{ ref('int_311_enriched') }}