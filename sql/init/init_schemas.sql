CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.nyc_311_complaints (
    unique_key BIGINT PRIMARY KEY,
    created_date TIMESTAMP,
    closed_date TIMESTAMP,
    agency VARCHAR(255),
    agency_name VARCHAR(255),
    complaint_type VARCHAR(255),
    descriptor VARCHAR(255),
    descriptor_2 VARCHAR(255),
    location_type VARCHAR(100),
    incident_zip VARCHAR(20),
    incident_address VARCHAR(500),
    street_name VARCHAR(255),
    address_type VARCHAR(100),
    city VARCHAR(100),
    status VARCHAR(50),
    resolution_description TEXT,
    resolution_action_updated_date TIMESTAMP,
    community_board VARCHAR(50),
    council_district TEXT,
    police_precinct VARCHAR(50),
    bbl VARCHAR(50),
    borough VARCHAR(50),
    x_coordinate_state_plane NUMERIC,
    y_coordinate_state_plane NUMERIC,
    open_data_channel_type VARCHAR(100),
    park_facility_name VARCHAR(255),
    park_borough VARCHAR(100),
    latitude NUMERIC,
    longitude NUMERIC,
    location TEXT,
    cross_street_1 VARCHAR(255),
    cross_street_2 VARCHAR(255),
    intersection_street_1 VARCHAR(255),
    intersection_street_2 VARCHAR(255),
    landmark VARCHAR(255),
    facility_type VARCHAR(255),
    bridge_highway_name VARCHAR(255),
    bridge_highway_segment VARCHAR(255),
    taxi_pick_up_location VARCHAR(255),
    bridge_highway_direction VARCHAR(50),
    road_ramp VARCHAR(255),
    vehicle_type VARCHAR(100),
    taxi_company_borough VARCHAR(100),
    due_date TIMESTAMP
);

CREATE TABLE raw.ingestion_metadata (
    source_name TEXT PRIMARY KEY,
    last_created_date TIMESTAMP,
    last_unique_key TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;