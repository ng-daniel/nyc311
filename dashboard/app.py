from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from components.charts import (
    daily_volume_chart,
    geo_heatmap_chart,
    top_complaint_types_chart,
)
from queries.dashboard_queries import (
    DashboardQueryError,
    get_daily_trends,
    get_geo_heatmap,
    get_overview_metrics,
    get_recent_complaints,
    get_top_complaint_types,
)


st.set_page_config(
    page_title="NYC 311 Operations Dashboard",
    page_icon="311",
    layout="wide",
)


def _format_timestamp(value: pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return "Unavailable"
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        # assume EST if no timezone is provided, since the data is from NYC
        timestamp = timestamp.tz_localize(ZoneInfo("America/New_York"))
    return timestamp.tz_convert("America/New_York").strftime("%Y-%m-%d %I:%M %p %Z")


def _status_label(last_ingestion_at: pd.Timestamp | None) -> tuple[str, str]:
    if last_ingestion_at is None or pd.isna(last_ingestion_at):
        return "Unknown", "No ingestion metadata was found."

    timestamp = pd.Timestamp(last_ingestion_at)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(timezone.utc)

    age = datetime.now(timezone.utc) - timestamp.to_pydatetime()
    if age.total_seconds() <= 24 * 3600:
        return "Healthy", f"Last ingestion ran {age.days} day(s) ago or less."
    if age.total_seconds() <= 72 * 3600:
        return "Stale", "Ingestion metadata is older than one day."
    return "Delayed", "Ingestion metadata is older than three days."


def _overview_header(metrics: dict[str, object]) -> None:
    status_label, status_help = _status_label(metrics.get("last_ingestion_at"))
    total_records = int(metrics.get("total_records") or 0)
    complaint_types = int(metrics.get("complaint_types") or 0)
    agencies = int(metrics.get("agencies") or 0)
    avg_resolution_hours = metrics.get("avg_resolution_hours")

    st.title("NYC 311 Operations Dashboard")
    st.caption("Interactive BI view powered by dbt mart tables in PostgreSQL.")

    metric_columns = st.columns(5)
    metric_columns[0].metric("Total Records", f"{total_records:,}")
    metric_columns[1].metric("Complaint Types", f"{complaint_types:,}")
    metric_columns[2].metric("Agencies", f"{agencies:,}")
    metric_columns[3].metric("Latest Complaint", _format_timestamp(metrics.get("latest_created_at")))
    metric_columns[4].metric(
        "Pipeline Status",
        status_label,
        help=status_help,
    )

    freshness_columns = st.columns(3)
    freshness_columns[0].metric("Last Ingestion", _format_timestamp(metrics.get("last_ingestion_at")))
    freshness_columns[1].metric("Ingestion Watermark", _format_timestamp(metrics.get("ingestion_watermark")))
    freshness_columns[2].metric(
        "Avg Resolution Hours",
        f"{float(avg_resolution_hours):.1f}" if avg_resolution_hours is not None and not pd.isna(avg_resolution_hours) else "N/A",
    )


def main() -> None:
    days = st.sidebar.select_slider(
        "Trend window",
        options=[7, 14, 30, 90, 180],
        value=30,
    )
    recent_limit = st.sidebar.select_slider(
        "Recent records",
        options=[10, 25, 50, 100],
        value=25,
    )

    try:
        with st.spinner("Loading dashboard metrics..."):
            metrics = get_overview_metrics()
            daily_trends = get_daily_trends(days)
            complaint_types = get_top_complaint_types(days)
            geo_points = get_geo_heatmap(days)
            recent_complaints = get_recent_complaints(limit=recent_limit)
    except DashboardQueryError as exc:
        st.error(str(exc))
        st.stop()

    _overview_header(metrics)

    trend_column, type_column = st.columns(2)
    trend_column.plotly_chart(daily_volume_chart(daily_trends), use_container_width=True)
    type_column.plotly_chart(top_complaint_types_chart(complaint_types), use_container_width=True)

    st.plotly_chart(geo_heatmap_chart(geo_points), use_container_width=True)

    st.subheader("Recent Complaints")
    st.caption("A bounded sample from the mart fact table. Use the Data Explorer page for filters.")
    st.dataframe(
        recent_complaints,
        use_container_width=True,
        hide_index=True,
        column_config={
            "resolution_hours": st.column_config.NumberColumn("Resolution Hours", format="%.1f"),
        },
    )


if __name__ == "__main__":
    main()