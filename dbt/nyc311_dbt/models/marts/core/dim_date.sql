{{ config(materialized='table') }}

with date_spine as (

    select
        generate_series(
            '2010-01-01'::date,
            '2035-12-31'::date,
            interval '1 day'
        )::date as date_day

),

final as (

    select
        date_day,

        extract(year from date_day)::int                as year,
        extract(quarter from date_day)::int             as quarter,
        extract(month from date_day)::int               as month,
        to_char(date_day, 'Month')                      as month_name,
        to_char(date_day, 'Mon')                        as month_abbrev,

        extract(week from date_day)::int                as week_of_year,
        extract(doy from date_day)::int                 as day_of_year,
        extract(day from date_day)::int                 as day_of_month,
        extract(dow from date_day)::int                 as day_of_week,

        to_char(date_day, 'Day')                        as day_name,
        to_char(date_day, 'Dy')                         as day_abbrev,

        (extract(dow from date_day) in (0,6))           as is_weekend,
        (date_day = date_trunc('month', date_day))      as is_month_start,
        (date_day = (date_trunc('month', date_day) 
                     + interval '1 month - 1 day')::date) as is_month_end,

        to_char(date_day, 'YYYY-MM')                    as year_month,
        to_char(date_day, 'IYYY-IW')                    as iso_year_week

    from date_spine

)

select * from final