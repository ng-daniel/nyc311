from __future__ import annotations

import os
from typing import Any

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv


load_dotenv()


class DashboardQueryError(RuntimeError):
    pass


def _database_host() -> str:
    return os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST") or "localhost"


def _database_config() -> dict[str, Any]:
    config = {
        "host": _database_host(),
        "port": int(os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT") or os.getenv("DBT_PORT") or 5432),
        "dbname": os.getenv("DB_NAME") or os.getenv("POSTGRES_DB") or os.getenv("DBT_DBNAME"),
        "user": os.getenv("DB_USER") or os.getenv("POSTGRES_USER") or os.getenv("DBT_USER"),
        "password": os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or os.getenv("DBT_PASS"),
    }
    missing = [key for key, value in config.items() if key in {"dbname", "user"} and not value]
    if missing:
        missing_names = ", ".join(missing)
        raise DashboardQueryError(
            f"Missing database configuration for: {missing_names}. Set DB_* or POSTGRES_* variables before running the dashboard."
        )
    return config


def _run_query(query: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    try:
        with psycopg2.connect(**_database_config()) as connection:
            return pd.read_sql_query(query, connection, params=params)
    except Exception as exc:
        raise DashboardQueryError(f"Dashboard query failed: {exc}") from exc


def _as_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


@st.cache_data(ttl=300)
def get_overview_metrics() -> dict[str, Any]:
    overview = _run_query(
        """
        with fact_stats as (
            select
                count(*) as total_records,
                count(distinct complaint_type) as complaint_types,
                count(distinct agency) as agencies,
                count(distinct borough) as boroughs,
                max(created_at) as latest_created_at,
                avg(resolution_hours) filter (where resolution_hours is not null) as avg_resolution_hours
            from marts.fct_311_complaints
        ),
        latest_ingestion as (
            select updated_at, last_created_date
            from raw.ingestion_metadata
            where source_name = 'nyc_311_complaints'
        )
        select
            fact_stats.total_records,
            fact_stats.complaint_types,
            fact_stats.agencies,
            fact_stats.boroughs,
            fact_stats.latest_created_at,
            fact_stats.avg_resolution_hours,
            latest_ingestion.updated_at as last_ingestion_at,
            latest_ingestion.last_created_date as ingestion_watermark
        from fact_stats
        left join latest_ingestion on true
        """
    )
    if overview.empty:
        return {
            "total_records": 0,
            "complaint_types": 0,
            "agencies": 0,
            "boroughs": 0,
            "latest_created_at": None,
            "avg_resolution_hours": None,
            "last_ingestion_at": None,
            "ingestion_watermark": None,
        }

    record = overview.iloc[0].to_dict()
    for key in ("latest_created_at", "last_ingestion_at", "ingestion_watermark"):
        record[key] = pd.to_datetime(record[key], errors="coerce")
        print(f"Converted {key} to timestamp: {record[key]}")
    return record


@st.cache_data(ttl=300)
def get_daily_trends(days: int) -> pd.DataFrame:
    daily_trends = _run_query(
        """
        select
            created_date,
            borough,
            sum(complaint_count) as complaint_count
        from marts.fct_311_daily
        where created_date >= current_date - (%s * interval '1 day')
        group by 1, 2
        order by 1 asc, 3 desc
        """,
        (days,),
    )
    if not daily_trends.empty:
        daily_trends["created_date"] = _as_timestamp(daily_trends["created_date"])
    return daily_trends


@st.cache_data(ttl=300)
def get_top_complaint_types(days: int, limit: int = 10) -> pd.DataFrame:
    return _run_query(
        """
        select
            complaint_type,
            sum(complaint_count) as complaint_count,
            sum(complaint_count * coalesce(avg_resolution_hours, 0))
                / nullif(sum(case when avg_resolution_hours is not null then complaint_count else 0 end), 0)
                as avg_resolution_hours
        from marts.fct_311_daily
        where created_date >= current_date - (%s * interval '1 day')
        group by 1
        order by 2 desc
        limit %s
        """,
        (days, limit),
    )


@st.cache_data(ttl=300)
def get_geo_heatmap(days: int, limit: int = 800) -> pd.DataFrame:
    geo_points = _run_query(
        """
        select
            latitude_rounded as latitude,
            longitude_rounded as longitude,
            sum(complaint_count) as complaint_count,
            avg(avg_resolution_hours) as avg_resolution_hours
        from marts.fct_311_geo_heatmap
        where created_date >= current_date - (%s * interval '1 day')
        group by 1, 2
        order by 3 desc
        limit %s
        """,
        (days, limit),
    )
    if not geo_points.empty:
        geo_points["location_label"] = geo_points.apply(
            lambda row: f"Lat {row['latitude']:.2f}, Lon {row['longitude']:.2f}",
            axis=1,
        )
    return geo_points


@st.cache_data(ttl=300)
def get_agency_performance(months: int, limit: int = 6) -> pd.DataFrame:
    agency_performance = _run_query(
        """
        with recent as (
            select
                agency,
                month,
                complaint_count,
                avg_resolution_hours
            from marts.fct_311_agency_performance
            where month >= date_trunc('month', current_date) - (%s * interval '1 month')
        ),
        ranked as (
            select
                agency,
                sum(complaint_count) as total_complaints
            from recent
            group by 1
            order by 2 desc
            limit %s
        )
        select
            recent.agency,
            recent.month,
            recent.complaint_count,
            recent.avg_resolution_hours
        from recent
        inner join ranked using (agency)
        order by recent.month asc, recent.complaint_count desc
        """,
        (months, limit),
    )
    if not agency_performance.empty:
        agency_performance["month"] = _as_timestamp(agency_performance["month"])
    return agency_performance


@st.cache_data(ttl=300)
def get_filter_options() -> dict[str, list[str]]:
    boroughs = _run_query(
        """
        select borough
        from marts.dim_borough
        where borough is not null and borough <> ''
        order by borough
        """
    )
    statuses = _run_query(
        """
        select distinct status
        from marts.fct_311_complaints
        where status is not null and status <> ''
        order by status
        """
    )
    agencies = _run_query(
        """
        select agency
        from marts.dim_agency
        where agency is not null and agency <> ''
        order by agency
        """
    )
    return {
        "boroughs": boroughs["borough"].tolist() if not boroughs.empty else [],
        "statuses": statuses["status"].tolist() if not statuses.empty else [],
        "agencies": agencies["agency"].tolist() if not agencies.empty else [],
    }


@st.cache_data(ttl=300)
def get_recent_complaints(
    limit: int,
    borough: str | None = None,
    status: str | None = None,
    agency: str | None = None,
) -> pd.DataFrame:
    clauses = []
    params: list[Any] = []

    if borough:
        clauses.append("borough = %s")
        params.append(borough)
    if status:
        clauses.append("status = %s")
        params.append(status)
    if agency:
        clauses.append("agency = %s")
        params.append(agency)

    where_clause = ""
    if clauses:
        where_clause = "where " + " and ".join(clauses)

    params.append(limit)
    recent = _run_query(
        f"""
        select
            unique_key,
            created_at,
            closed_at,
            borough,
            agency,
            complaint_type,
            status,
            resolution_hours
        from marts.fct_311_complaints
        {where_clause}
        order by created_at desc
        limit %s
        """,
        tuple(params),
    )
    if not recent.empty:
        recent["created_at"] = _as_timestamp(recent["created_at"])
        recent["closed_at"] = _as_timestamp(recent["closed_at"])
    return recent