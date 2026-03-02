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

        date_trunc('day', created_at) as created_date,

        round(cast(latitude as numeric), 2) as latitude_rounded,
        round(cast(longitude as numeric), 2) as longitude_rounded

    from base

)

select * from enriched