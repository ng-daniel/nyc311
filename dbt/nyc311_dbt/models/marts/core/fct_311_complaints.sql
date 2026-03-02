select
    unique_key,
    created_at,
    closed_at,
    created_date,
    is_instant_close,

    borough,
    agency,
    complaint_type,
    status,

    resolution_hours,
    resolution_bucket,

    has_location_data,
    latitude,
    longitude,
    latitude_rounded,
    longitude_rounded

from {{ ref('int_311_enriched') }}