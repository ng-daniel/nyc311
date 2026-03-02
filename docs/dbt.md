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
