with base as (

    select * from {{ ref('stg_nyc_311_complaints') }}

),

enriched as (

    select
        *,

        case 
            when resolution_hours <= 24 then 'under_24h'
            when resolution_hours <= 72 then '1-3_days'
            else 'over_3_days'
        end as resolution_bucket,

        (closed_at is not null and closed_at = created_at) AS is_instant_close,
        date_trunc('day', created_at) as created_date,

        (latitude is not null and longitude is not null) AS has_location_data,

        round(cast(latitude as numeric), 2) as latitude_rounded,
        round(cast(longitude as numeric), 2) as longitude_rounded

    from base

)

select * from enriched