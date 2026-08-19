from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        showarrow=False,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        font={"size": 16},
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.update_layout(
        template="plotly_white",
        height=420,
        margin={"l": 16, "r": 16, "t": 48, "b": 16},
    )
    return figure


def daily_volume_chart(daily_trends: pd.DataFrame) -> go.Figure:
    if daily_trends.empty:
        return _empty_figure("No daily trend data available for the selected window.")

    figure = px.line(
        daily_trends,
        x="created_date",
        y="complaint_count",
        color="borough",
        title="Complaint Volume Over Time",
        labels={
            "created_date": "Date",
            "complaint_count": "Complaints",
            "borough": "Borough",
        },
    )
    figure.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="Borough",
        margin={"l": 16, "r": 16, "t": 56, "b": 16},
    )
    figure.update_traces(mode="lines")
    return figure


def top_complaint_types_chart(complaint_types: pd.DataFrame) -> go.Figure:
    if complaint_types.empty:
        return _empty_figure("No complaint-type aggregate data available.")

    display_frame = complaint_types.sort_values("complaint_count", ascending=True)
    figure = px.bar(
        display_frame,
        x="complaint_count",
        y="complaint_type",
        orientation="h",
        color="avg_resolution_hours",
        color_continuous_scale="Sunset",
        title="Top Complaint Types",
        labels={
            "complaint_count": "Complaints",
            "complaint_type": "Complaint Type",
            "avg_resolution_hours": "Avg Resolution Hours",
        },
    )
    figure.update_layout(
        template="plotly_white",
        coloraxis_colorbar_title="Avg Resolution Hours",
        margin={"l": 16, "r": 16, "t": 56, "b": 16},
    )
    return figure


def geo_heatmap_chart(geo_points: pd.DataFrame) -> go.Figure:
    if geo_points.empty:
        return _empty_figure("No geographic data available for the selected window.")

    figure = px.scatter_map(
        geo_points,
        lat="latitude",
        lon="longitude",
        size="complaint_count",
        color="avg_resolution_hours",
        hover_name="location_label",
        hover_data={
            "complaint_count": ":,.0f",
            "avg_resolution_hours": ":.1f",
            "latitude": False,
            "longitude": False,
        },
        color_continuous_scale="Turbo",
        map_style="carto-positron",
        zoom=9.7,
        center={"lat": 40.7128, "lon": -74.0060},
        title="Geographic Hotspots",
    )
    figure.update_layout(
        margin={"l": 16, "r": 16, "t": 56, "b": 16},
        coloraxis_colorbar_title="Avg Resolution Hours",
    )
    return figure


def agency_performance_chart(agency_performance: pd.DataFrame) -> go.Figure:
    if agency_performance.empty:
        return _empty_figure("No agency performance data available.")

    figure = px.line(
        agency_performance,
        x="month",
        y="complaint_count",
        color="agency",
        markers=True,
        title="Monthly Agency Workload",
        labels={
            "month": "Month",
            "complaint_count": "Complaints",
            "agency": "Agency",
        },
    )
    figure.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="Agency",
        margin={"l": 16, "r": 16, "t": 56, "b": 16},
    )
    return figure