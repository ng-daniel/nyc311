import os
import time
import logging
from io import StringIO
from typing import List, Dict

import requests
from dotenv import load_dotenv
import polars as pl
import psycopg2

load_dotenv()

API_URL = os.getenv("NYC_311_URL")
APP_KEY = os.getenv("NYC_OD_APP_TOKEN")

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")

BATCH_SIZE = 100000
EXPECTED_COLUMNS = ['unique_key', 'created_date', 'closed_date', 'agency', 'agency_name',
       'complaint_type', 'descriptor', 'descriptor_2', 'location_type',
       'incident_zip', 'incident_address', 'street_name', 'address_type',
       'city', 'status', 'resolution_description',
       'resolution_action_updated_date', 'community_board', 'council_district',
       'police_precinct', 'bbl', 'borough', 'x_coordinate_state_plane',
       'y_coordinate_state_plane', 'open_data_channel_type',
       'park_facility_name', 'park_borough', 'latitude', 'longitude',
       'location', 'cross_street_1', 'cross_street_2', 'intersection_street_1',
       'intersection_street_2', 'landmark', 'facility_type',
       'bridge_highway_name', 'bridge_highway_segment',
       'taxi_pick_up_location', 'bridge_highway_direction', 'road_ramp',
       'vehicle_type', 'taxi_company_borough', 'due_date']

logging.basicConfig(level=logging.INFO)


def extract_batch(session, headers, limit, last_key) -> List[Dict]:
    """
    Extract a batch of data from the NYC 311 API.

    Args:
        session: The requests session object.
        headers: The headers to include in the request.
        last_key: The last unique key processed.
        limit: The maximum number of records to fetch.

    Returns:
        A list of dictionaries containing the batch of data.
    """
    params = {
        "$order": "unique_key",
        "$limit": limit,
        "$select": "*"
    }
    if last_key:
        params["$where"] = f"unique_key > '{last_key}'"
    
    response = session.get(
        API_URL,
        headers=headers,
        params=params,
        timeout=30
    )
    if response.status_code == 429: # retry logic
        time.sleep(2)
        return extract_batch(session, headers, last_key, limit)
    
    response.raise_for_status()
    return response.json()


def normalize_batch_dicts(data: list[dict], columns: list[str]) -> pl.DataFrame:
    """
    Normalize a batch of data represented as a list of dictionaries.
    Reorders columns by first adding those that are present in the data, 
    then adding any missing columns with null values.
    
    Args:
        data: A list of dictionaries, where each dictionary represents a row of data.
        columns: A list of column names to ensure are present in the output.
    
    Returns:
        A list of lists, where each inner list represents a row of data with values corresponding to the specified columns.
    """

    df = pl.DataFrame(data)
    df = df.select([col for col in columns if col in df.columns] + 
                   [col for col in columns if col not in df.columns])
    
    for col in columns:
        if col not in df.columns:
            df = df.with_columns(pl.lit(None).alias(col))
    return df

def load_batch(db_connection, df: pl.DataFrame, table_name: str) -> None:
    """
    Bulk load Polars DataFrame into Postgres via COPY

    Args:
        db_connection: A psycopg2 connection object to the Postgres database.
        df: A Polars DataFrame containing the data to be loaded.
        table_name: The name of the target table in the Postgres database.
    
    Returns:
        None
    """
    buffer = StringIO()
    df.write_csv(buffer, include_header=False)
    buffer.seek(0)

    with db_connection.cursor() as db_cursor:
        db_cursor.copy_expert(
            f"""
            COPY {table_name} ({', '.join(df.columns)}) 
            FROM STDIN 
            WITH CSV
            """,
            buffer)
    db_connection.commit()

def get_max_existing_key(db_connection, table_name: str) -> str | None:
    """
    Get the maximum existing unique key from the target table in Postgres.

    Args:
        db_connection: A psycopg2 connection object to the Postgres database.
        table_name: The name of the target table in the Postgres database.
    
    Returns:
        The maximum unique key as a string, or None if the table is empty.
    """
    with db_connection.cursor() as db_cursor:
        db_cursor.execute(
            f"""
            SELECT max(unique_key) 
            FROM {table_name}
            """)
        result = db_cursor.fetchone()[0]
    return result

