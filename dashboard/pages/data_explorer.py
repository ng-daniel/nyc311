from __future__ import annotations

import streamlit as st

from components.charts import agency_performance_chart
from queries.dashboard_queries import (
    DashboardQueryError,
    get_agency_performance,
    get_filter_options,
    get_recent_complaints,
)


st.set_page_config(
    page_title="NYC 311 Data Explorer",
    page_icon="311",
    layout="wide",
)


def main() -> None:
    st.title("Data Explorer")
    st.caption("Slice recent complaints without pulling the full dataset into Streamlit.")

    try:
        filter_options = get_filter_options()
    except DashboardQueryError as exc:
        st.error(str(exc))
        st.stop()

    filter_columns = st.columns(4)
    borough = filter_columns[0].selectbox("Borough", ["All"] + filter_options["boroughs"])
    status = filter_columns[1].selectbox("Status", ["All"] + filter_options["statuses"])
    agency = filter_columns[2].selectbox("Agency", ["All"] + filter_options["agencies"])
    limit = filter_columns[3].select_slider("Rows", options=[25, 50, 100, 250], value=50)

    performance_months = st.select_slider("Agency trend window", options=[3, 6, 12], value=6)

    borough_filter = None if borough == "All" else borough
    status_filter = None if status == "All" else status
    agency_filter = None if agency == "All" else agency

    try:
        with st.spinner("Loading filtered mart data..."):
            recent_complaints = get_recent_complaints(
                limit=limit,
                borough=borough_filter,
                status=status_filter,
                agency=agency_filter,
            )
            agency_performance = get_agency_performance(months=performance_months)
    except DashboardQueryError as exc:
        st.error(str(exc))
        st.stop()

    st.plotly_chart(agency_performance_chart(agency_performance), use_container_width=True)

    st.subheader("Filtered Recent Complaints")
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