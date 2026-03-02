with source as (

    select * 
    from {{ source('raw', 'nyc_311_complaints') }}

),

cleaned as (

    select
        unique_key                           as unique_key,
        created_date                         as created_at,
        closed_date                          as closed_at,
        due_date                             as due_at,

        agency,
        agency_name,

        complaint_type,
        descriptor                           as complaint_subtype,
        descriptor_2,

        borough,
        incident_zip                         as zip_code,
        city,

        status,
        resolution_description,
        resolution_action_updated_date       as resolution_updated_at,

        latitude::double precision           as latitude,
        longitude::double precision          as longitude,

        council_district,
        police_precinct,
        community_board,

        open_data_channel_type               as submission_channel,

        case
            when closed_date is not null
            then extract(epoch from (closed_date - created_date)) / 3600
        end                                  as resolution_hours

    from source

    where unique_key is not null

)

select * from cleaned