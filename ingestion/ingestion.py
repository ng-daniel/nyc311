import os
import time
import logging
import subprocess
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
DB_PORT = os.getenv("POSTGRES_PORT", 5432)

BATCH_SIZE = 10000

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


def extract_batch(session, headers, limit, last_key, override_params: dict = None) -> List[Dict]:
    """
    Extract a batch of data from the NYC 311 API.

    Args:
        session: The requests session object.
        headers: The headers to include in the request.
        last_key: The last unique key processed.
        limit: The maximum number of records to fetch.
        override_params: Additional custom parameters to include in the request, which will override the default parameters.

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
    if override_params:
        params = override_params
    
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
    Reorders columns by first adding any missing columns with null values,
    then selecting only the expected columns in the specified order.
    
    Args:
        data: A list of dictionaries, where each dictionary represents a row of data.
        columns: A list of column names to ensure are present in the output.
    
    Returns:
        A Polars DataFrame with columns ordered according to the specified list, 
        including any missing columns filled with null values.
    """
    
    print(data)
    df = pl.DataFrame(data, strict=False)
    print(df.select(['created_date', 'closed_date']).sort(by=['created_date'], descending=True).head())

    for col in columns:
        if col not in df.columns:
            df = df.with_columns(pl.lit(None).alias(col))
    
    date_columns = ['created_date', 'closed_date', 'resolution_action_updated_date', 'due_date']
    for col in date_columns:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.Datetime))

    df = df.select(columns)
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
            WITH CSV NULL ''
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

def ingest_pipeline() -> None:
    """
    Runs the full ingestion pipeline.

    1. Opens a session with the API, and a connection to the postgresql database
    2. Extract a batch of data, either starting from the beginning or the last 
        unique key in the database.
    3. Normalize the data by ensuring all columns align with the expected ones.
        Ignore unexpected columns and set missing expected columns to null.
    4. Using the database connection and the resulting normalized df,
        write the csv as bytes to a buffer and append that data to the
        raw/bronze layer.
    """

    TABLE_NAME = "raw.nyc_311_complaints"
    
    session = requests.Session()
    db_connection = psycopg2.connect(
        host="localhost",
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    headers = { 
        'X-App-Token': APP_KEY 
    }

    last_key = get_max_existing_key(db_connection, TABLE_NAME)
    total_rows = 0

    while True:
        data = extract_batch(session, headers, BATCH_SIZE, None) # last_key)
        if not data:
            logging.info("No more rows to ingest.")
            break
            
        df = normalize_batch_dicts(data, EXPECTED_COLUMNS)
        print(df.select(['created_date', 'closed_date']).sort(by=['created_date'], descending=True).head())

        for col in df.columns:
            if isinstance(df[col].dtype, (pl.Struct, pl.List)):
                df = df.with_columns(pl.col(col).cast(pl.Utf8))

        print(df.select(['created_date', 'closed_date']).sort(by=['created_date'], descending=True).head())
        load_batch(db_connection, df, TABLE_NAME)

        last_key = df["unique_key"][-1]
        total_rows += df.height

        logging.info(f"Loaded {df.height} rows. Session total: {total_rows}. Last key: {last_key}")
    
        break

    db_connection.close()
    session.close()

def ingest_sample(size: int, last_key: int | None = None) -> None:
    """
    Ingest a recent sample of data from the NYC 311 API and write it to a CSV file.

    Args:
        size: The number of records to ingest.
    
    Returns:
        None
    """
    session = requests.Session()
    headers = { 
        'X-App-Token': APP_KEY 
    }
    if last_key:
        params = {
            "$select": "*",
            "$limit": size,
            "$where": f"unique_key = '{last_key}'"
        }
    else:
        params = {
            "$select": "*",
            "$limit": size,
        }
    data = extract_batch(session, headers, size, None, override_params=params)
    if not data:
        logging.info("ingest_sample -> no data available to ingest")
        return
    df_raw = pl.DataFrame(data)
    df_norm = normalize_batch_dicts(data, EXPECTED_COLUMNS)
    
    # cast nested/struct columns (like GeoJSON point data) to strings
    for col in df_raw.columns:
        if isinstance(df_raw[col].dtype, (pl.Struct, pl.List)):
            df_raw = df_raw.with_columns(pl.col(col).cast(pl.Utf8))
    for col in df_norm.columns:
        if isinstance(df_norm[col].dtype, (pl.Struct, pl.List)):
            df_norm = df_norm.with_columns(pl.col(col).cast(pl.Utf8))

    df_raw.write_csv("./ingestion/sample_raw.csv")
    df_norm.write_csv("./ingestion/sample_norm.csv")

if __name__ == "__main__":
    # ingest_pipeline()
    ingest_sample(1000, last_key=42306178)


