3/1/26 - dbt structure

```
+---models
|   |   sources.yml
|   |
|   +---intermediate
|   |       int_311_enriched.sql
|   |
|   +---marts
|   |   +---aggregates
|   |   |       fct_311_agency_performance.sql
|   |   |       fct_311_daily.sql
|   |   |       fct_311_geo_heatmap.sql
|   |   |
|   |   \---core
|   |           dim_agency.sql
|   |           dim_borough.sql
|   |           dim_complaint_type.sql
|   |           dim_date.sql
|   |           fct_311_complaints.sql
|   |
|   \---staging
|           stg_nyc_311_complaints.sql
|           _staging.yml
```

## HOW TO RUN

1. Make sure postgres datbase is running

```
docker compose up
```

2. Make sure packages are up to date and everything looks good

```
docker compose run --rm dbt deps
docker compose run --rm dbt debug
```

3. Run this command to update tables through

```
docker compose run --rm dbt build
```
