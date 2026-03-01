import os
import time
import logging
from io import StringIO
from typing import List, Dict, Optional
from datetime import datetime

import requests
from dotenv import load_dotenv
import polars as pl
import psycopg2

load_dotenv()

logging.basicConfig(level=logging.INFO)


class NYC311Ingestion:
    """
    Manages the extraction, normalization, and loading of NYC 311 complaint data
    from the Socrata API to PostgreSQL.
    """

    EXPECTED_COLUMNS = [
        'unique_key', 'created_date', 'closed_date', 'agency', 'agency_name',
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
        'vehicle_type', 'taxi_company_borough', 'due_date'
    ]

    def __init__(self, 
                batch_size:int = 1000):
        """Initialize NYC311 ingestion with configuration from environment variables."""
        self.api_url = os.getenv("NYC_311_URL")
        self.app_key = os.getenv("NYC_OD_APP_TOKEN")
        
        self.db_name = os.getenv("POSTGRES_DB")
        self.db_user = os.getenv("POSTGRES_USER")
        self.db_pass = os.getenv("POSTGRES_PASSWORD")
        self.db_port = os.getenv("POSTGRES_PORT", 5432)

        self.batch_size = batch_size
        self.table_name = "raw.nyc_311_complaints"
        self.source_name = "nyc_311_complaints"
        self.metadata_table_name = "raw.ingestion_metadata"
        self.session = None
        self.db_connection = None

    def __enter__(self):
        """Context manager entry: initialize session and database connection."""
        self.session = requests.Session()
        self.db_connection = psycopg2.connect(
            host="localhost",
            database=self.db_name,
            user=self.db_user,
            password=self.db_pass,
            port=self.db_port
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: close session and database connection."""
        if self.db_connection:
            self.db_connection.close()
        if self.session:
            self.session.close()

    def extract_batch(
        self,
        limit: int,
        last_created_date: Optional[datetime] = None,
        last_unique_key: Optional[str] = None,
        override_params: Optional[dict] = None,
    ) -> List[Dict]:
        """
        Extract a batch of data from the NYC 311 API using a
        (created_date, unique_key) watermark strategy.

        If a last_created_date and last_unique_key are provided, the method will fetch records where:
        - main:         created_date is greater than last_created_date, OR
        - tiebreaker:   created_date is equal to last_created_date AND unique_key is greater than last_unique_key
        
        Implements this using a double request approach for efficiency 
        while still capping records at limit by setting the limit of main query
        to `overall limit` - `number of tiebreaker rows`. 

        If neither last_created_date or last_unique_key exist, 

        Args:
            limit: Maximum number of records to fetch.
            last_created_date: Last created_date watermark for filtering.
            last_unique_key: Last unique_key watermark for filtering.
            override_params: Custom parameters to override defaults.
        
        Returns:
            A list of dictionaries containing the batch of data.
        """
        
        headers = {'X-App-Token': self.app_key}
        params = {
            "$order": "created_date ASC, unique_key ASC",
            "$select": "*"
        }
        if override_params:
            params.update(override_params)
        
        n_retries = 3
        timeout_sec = 30
        tiebreaker_data: List[Dict] = []
        main_data: List[Dict] = []

        if last_unique_key and last_created_date:
            iso_ts = last_created_date.strftime("%Y-%m-%dT%H:%M:%S.000")
            params["$where"] = f"created_date > '{iso_ts}'"
            
            params_tiebreaker = params.copy()
            params_tiebreaker["$where"] = (
                f"created_date = '{iso_ts}' " 
                f"AND unique_key > '{last_unique_key}'"
            )
            params_tiebreaker["$limit"] = limit

            for attempt in range(n_retries):
                response = self.session.get(
                    self.api_url,
                    headers=headers,
                    params=params_tiebreaker, # uses tiebreaker params instead
                    timeout=timeout_sec
                )
                if response.status_code == 429:
                    time.sleep(2 ** (attempt + 1))  # Exponential backoff
                    continue
                response.raise_for_status()
                tiebreaker_data = response.json()
                break
            else:
                raise RuntimeError("Max retries exceeded for API tiebreaker extraction.")
        elif last_created_date: # this case typically only runs for the start_date override scenario
            iso_ts = last_created_date.strftime("%Y-%m-%dT%H:%M:%S.000")
            params["$where"] = f"created_date >= '{iso_ts}'"

        remaining = max(0, limit - len(tiebreaker_data))
        if remaining > 0:
            params["$limit"] = remaining
            for attempt in range(n_retries):
                response = self.session.get(
                    self.api_url,
                    headers=headers,
                    params=params, # uses main params for main query
                    timeout=timeout_sec
                )
                if response.status_code == 429:
                    time.sleep(2 ** (attempt + 1))  # Exponential backoff
                    continue
                response.raise_for_status()
                main_data = response.json()
                break
            else:
                raise RuntimeError("Max retries exceeded for API main extraction.")
        
        tiebreaker_data.extend(main_data)
        return tiebreaker_data

    def normalize_batch_dicts(self, data: list[dict]) -> pl.DataFrame:
        """
        Normalize a batch of data represented as a list of dictionaries.
        Reorders columns by first adding any missing columns with null values,
        then selecting only the expected columns in the specified order.
        
        Args:
            data: A list of dictionaries, where each dictionary represents a row of data.
        
        Returns:
            A Polars DataFrame with columns ordered according to EXPECTED_COLUMNS,
            including any missing columns filled with null values.
        """
        df = pl.DataFrame(data, strict=False)

        for col in self.EXPECTED_COLUMNS:
            if col not in df.columns:
                df = df.with_columns(pl.lit(None).alias(col))
        
        date_columns = ['created_date', 'closed_date', 'resolution_action_updated_date', 'due_date']
        for col in date_columns:
            if col in df.columns:
                df = df.with_columns(pl.col(col).cast(pl.Datetime))

        df = df.select(self.EXPECTED_COLUMNS)
        return df

    def load_batch(self, df: pl.DataFrame) -> None:
        """
        Bulk load Polars DataFrame into Postgres via COPY.

        Args:
            df: A Polars DataFrame containing the data to be loaded.
        
        Returns:
            None
        """

        if df.is_empty():
            logging.warning("Requested batch load for empty dataframe, probably shouldn't happen, go check that out.")
            return 
        df = df.unique(subset=["unique_key"])

        buffer = StringIO()
        df.write_csv(buffer, include_header=False)
        buffer.seek(0)
        
        temp_table_name = f"tmp_{self.source_name}_batch"
        with self.db_connection.cursor() as db_cursor:
            db_cursor.execute(
                f"""
                DROP TABLE IF EXISTS {temp_table_name};
                CREATE TEMP TABLE {temp_table_name} (LIKE {self.table_name} INCLUDING ALL)
                """
            )
            db_cursor.copy_expert(
                f"""
                COPY {temp_table_name} ({', '.join(df.columns)}) 
                FROM STDIN 
                WITH CSV 
                NULL ''
                """,
                buffer
            )
            db_cursor.execute(
                f"""
                INSERT INTO {self.table_name} ({', '.join(df.columns)})
                SELECT * FROM {temp_table_name}
                ON CONFLICT (unique_key) DO NOTHING
                """
            )
            
            # update ingestion metadata with the latest date/key pair seen in this batch
            # handle conflicts by taking the max of the created_date, and then using the 
            # unique_key as a tiebreaker if created_date is the same
            db_cursor.execute(
                f"""
                WITH max_row AS (
                    SELECT created_date, unique_key
                    FROM {temp_table_name}
                    ORDER BY created_date DESC, unique_key DESC
                    LIMIT 1
                )
                INSERT INTO {self.metadata_table_name} (source_name, last_created_date, last_unique_key)
                SELECT '{self.source_name}', created_date, unique_key FROM max_row
                ON CONFLICT (source_name) DO UPDATE
                SET
                    last_created_date = GREATEST(
                        ingestion_metadata.last_created_date,
                        EXCLUDED.last_created_date
                    ),
                    last_unique_key = CASE
                        WHEN EXCLUDED.last_created_date > ingestion_metadata.last_created_date
                            THEN EXCLUDED.last_unique_key
                        WHEN EXCLUDED.last_created_date = ingestion_metadata.last_created_date
                            THEN GREATEST(
                                ingestion_metadata.last_unique_key,
                                EXCLUDED.last_unique_key
                            )
                        ELSE ingestion_metadata.last_unique_key
                    END,
                    updated_at = NOW()
                """
            )
        self.db_connection.commit()

    from datetime import datetime

    def get_latest_date_key(self) -> tuple[datetime | None, str | None]:
        """
        Get the last processed (created_date, unique_key) from metadata table.

        Returns:
            Tuple of (last_created_date as datetime, last_unique_key as string)
            or (None, None) if table is empty.
        """
        with self.db_connection.cursor() as db_cursor:
            db_cursor.execute(
                f"""
                SELECT m.last_created_date, m.last_unique_key
                FROM {self.metadata_table_name} m
                WHERE source_name = '{self.source_name}'
                """
            )
            result = db_cursor.fetchone()

        # handle case where metadata table is empty or source_name not found
        if result is None or result[0] is None:
            return (None, None)

        last_created_date, last_unique_key = result[0], result[1]
        if isinstance(last_created_date, str):
            last_created_date = datetime.fromisoformat(last_created_date)

        return last_created_date, last_unique_key

    def run_ingest_pipeline(self, start_date: Optional[datetime]) -> None:
        """
        Runs the full ingestion pipeline.

        1. Extract batches of data from the API, starting from the last ingested key.
        2. Normalize the data by ensuring all columns align with expected ones.
           Ignore unexpected columns and set missing expected columns to null.
        3. Cast nested/struct columns to strings and load the normalized data
           into the raw/bronze layer via PostgreSQL COPY.
        """
        last_date, last_key = self.get_latest_date_key()
        if start_date and (not last_date or start_date > last_date):
            last_date, last_key = start_date, None
            logging.info(f"Starting ingestion at provided start_date: {last_date}.")
        elif last_date and last_key:
            logging.info(f"Starting ingestion at date: {last_date} with key {last_key}")
        else:
            logging.info("Starting ingestion with no existing watermark (full table scan)")

        total_rows = 0
        while True:
            data = self.extract_batch(self.batch_size, last_created_date=last_date, last_unique_key=last_key)
            if not data:
                logging.info("No more rows to ingest.")
                break
                
            df = self.normalize_batch_dicts(data)

            # cast any nested/struct columns (like GeoJSON point data) to strings before loading
            for col in df.columns:
                if isinstance(df[col].dtype, (pl.Struct, pl.List)):
                    df = df.with_columns(pl.col(col).cast(pl.Utf8))

            self.load_batch(df)

            last_row = df.sort(["created_date", "unique_key"]).tail(1)
            last_date = last_row["created_date"][0]
            last_key = last_row["unique_key"][0]
            total_rows += df.height

            logging.info(f"Loaded {df.height} rows. Session total: {total_rows}. Latest record: {last_date} {last_key}")

            # rescan for next loop
            last_date, last_key = self.get_latest_date_key()

         
    def ingest_sample(self, size: int, last_key: int | None = None) -> None:
        """
        Ingest a recent sample of data from the NYC 311 API and write it to CSV files.

        Args:
            size: The number of records to ingest.
            last_key: Optional unique_key to filter specific record.
        
        Returns:
            None
        """
        session = requests.Session()
        headers = {'X-App-Token': self.app_key}
        
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
        
        data = self.extract_batch(size, override_params=params)
        if not data:
            logging.info("ingest_sample -> no data available to ingest")
            return
        
        df_raw = pl.DataFrame(data)
        df_norm = self.normalize_batch_dicts(data)
        
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
    
    start_date = datetime(2026, 1, 1)  # Example start date for backfill; set to None to use metadata watermark
    with NYC311Ingestion(batch_size=100000) as ingestion:
        ingestion.run_ingest_pipeline(start_date=start_date)