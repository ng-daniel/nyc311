# NYC 311 Data Engineering and Analytics Pipeline

## Overview

This project implements an end-to-end ELT pipeline for NYC 311 service request data. The pipeline ingests raw data from the NYC Open Data API, transforms and enriches it using dbt, and produces BI-ready aggregates for analysis of complaints trends, agency performance, and geospatial distribution.

## Architecture & Workflow

### Pipeline

```
NYC 311 API → Polars → PostgreSQL (raw schema) → dbt staging → dbt intermediate → dbt marts → BI layer
```

### Warehouse Architecture

- **Raw Layer (`raw`)** - stores raw API data without modifications
- **Staging Layer (`staging`)** - cleans and normalizes columns, enforces types, derives basic fields
- **Intermediate Layer (`intermediate`)** - enriches data with derived metrics and flags (e.g., `resolution_hours`, `is_instant_close`)
- **Marts Layer (`marts`)** - Star schema fact and dim tables, plus pre-aggregated tables for performance

## Key Features

### Ingestion Layer

- **Incremental Data Ingestion** - batched ingestion, query decomposition, metadata watermarking to maintain state between batches
- **Reliable Data Loading** - bulk inserts via temporary tables + `COPY`, with `ON CONFLICT DO NOTHING` to prevent duplicates.

### Transformation Layer

- **Data Quality Checks** - automated dbt tests to ensure data quality, such as `not_null`, `unique`, and `accepted_values`.
- **Derived Metrics & Flags** - includes `resolution_hours`, `is_instant_close` (auto-closure indicator), and other enriched fields.
- **Performance Optimization** - pre-aggregated tables for geospatial heatmaps, performance by agency, and daily trends.
- **Schema Organization** - medallion architecture; layered schemas (`staging`, `intermediate`, `marts`) maintain ground truth and provide clarity.

### Portability

- **Dockerized Environment** - dbt and PostgreSQL fully containerized for reproducibility and easy deployment.

## Technologies

- Python, Polars (ingestion and data manipulation)
- PostgreSQL (data warehouse)
- dbt (transformations, modeling, testing)
- Docker (containerized environment)
- NYC Open Data API (data source)

## Next Steps

- Connect a BI tool for dashboards (geo heatmaps, trends, agency/borough comparisons)
- Connect with multiple data sources (weather, other NYC APIs) to enrich data further and increase analytics capability

## Usage

1. Configure environment variables in `.env` for Postgres connection.
2. Build and run containers via Docker Compose:

```bash
docker compose up -d
```

3. Run ingestion pipeline into raw data table.
    - Starts at 1/1/2026 OR last ingested row. 

```bash
uv run -- python ingestion/ingestion.py
```

4. Run dbt tests and transformations

```bash
docker compose run --rm dbt deps
docker compose run --rm dbt build
docker compose run --rm dbt test
```

5. Use psql to explore and analyze data

```bash
docker exec -it nyc311_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
```

## Summary

- Ingestion and raw layer fully implemented and verified
- Staging, intermediate, and marts models implemented with dbt tests passing
- Incremental ingestion, metadata watermarking, and batch performance optimized
- Still need to work on BI layer (dashboards + visualizations), which will involve tweaking the mart models to fit analysis needs
