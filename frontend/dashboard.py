"""Dashboard rendering and filter helpers for a completed analysis state."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def state_frame(state: dict[str, Any]) -> pd.DataFrame:
    """Return the cleaned records held in a completed analysis state."""

    return pd.DataFrame(state.get("data_records", []))


def filter_candidates(frame: pd.DataFrame, metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    """Choose one useful date and segment control; avoid a dense filter panel."""

    date_column = next((column for column in metadata.get("date_columns", []) if column in frame), None)
    category_column = next(
        (
            column
            for column in metadata.get("categorical_columns", [])
            if column in frame and 2 <= frame[column].nunique(dropna=True) <= 12 and column != date_column
        ),
        None,
    )
    return date_column, category_column


def apply_filters(
    frame: pd.DataFrame,
    date_column: str | None,
    date_range: tuple[object, object] | None,
    category_column: str | None,
    category_values: list[object] | None,
) -> pd.DataFrame:
    """Apply the dashboard-wide date and segment controls to a data copy."""

    filtered = frame.copy()
    if date_column and date_range and date_column in filtered:
        dates = pd.to_datetime(filtered[date_column], errors="coerce", format="mixed")
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered = filtered.loc[dates.between(start, end, inclusive="both")].copy()
    if category_column and category_values and category_column in filtered:
        filtered = filtered[filtered[category_column].isin(category_values)].copy()
    return filtered


def _number(value: float | int) -> str:
    return f"{value:,.2f}" if isinstance(value, float) and not value.is_integer() else f"{value:,}"


def _render_kpis(frame: pd.DataFrame, profile: dict[str, Any]) -> None:
    st.subheader("Overview")
    completeness = 100.0 if frame.empty else (1 - frame.isna().mean().mean()) * 100
    columns = st.columns(4)
    columns[0].metric("Records shown", f"{len(frame):,}")
    columns[1].metric("Columns", f"{len(frame.columns):,}")
    columns[2].metric("Completeness", f"{completeness:.1f}%")
    columns[3].metric("Source duplicates", f"{profile.get('duplicate_rows', 0):,}")

    numeric = frame.select_dtypes(include="number")
    if not numeric.empty:
        st.caption(
            "Headline numeric averages: "
            + " · ".join(f"{column} {_number(float(numeric[column].mean()))}" for column in numeric.columns[:3])
        )


def _render_chart(frame: pd.DataFrame, spec: dict[str, Any]) -> None:
    chart_type = spec["type"]
    title = spec["title"]
    if chart_type == "histogram" and spec["x"] in frame:
        figure = px.histogram(frame, x=spec["x"], title=title, color_discrete_sequence=["#2563eb"])
    elif chart_type == "bar" and {spec["x"], spec["y"]} <= set(frame.columns):
        grouped = frame.groupby(spec["x"], dropna=False)[spec["y"]].mean().sort_values(ascending=False).reset_index()
        figure = px.bar(grouped, x=spec["x"], y=spec["y"], title=title, color_discrete_sequence=["#2563eb"])
    elif chart_type == "heatmap":
        numeric = frame.select_dtypes(include="number")
        if len(numeric.columns) < 2:
            return
        correlation = numeric.corr().round(2)
        figure = go.Figure(
            go.Heatmap(
                z=correlation.values,
                x=correlation.columns,
                y=correlation.index,
                colorscale="Blues",
                zmin=-1,
                zmax=1,
                colorbar={"title": "Pearson r"},
            )
        )
        figure.update_layout(title=title)
    elif chart_type == "scatter" and {spec["x"], spec["y"]} <= set(frame.columns):
        figure = px.scatter(frame, x=spec["x"], y=spec["y"], title=title, color_discrete_sequence=["#2563eb"])
    elif chart_type == "line" and {spec["x"], spec["y"]} <= set(frame.columns):
        plotted = frame[[spec["x"], spec["y"]]].copy()
        plotted[spec["x"]] = pd.to_datetime(plotted[spec["x"]], errors="coerce", format="mixed")
        plotted = plotted.dropna().sort_values(spec["x"])
        if plotted.empty:
            return
        figure = px.line(plotted, x=spec["x"], y=spec["y"], title=title, markers=True, color_discrete_sequence=["#2563eb"])
    else:
        return

    figure.update_layout(
        template="plotly_white",
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        legend_title_text="",
    )
    st.plotly_chart(figure, use_container_width=True, config={"displaylogo": False})


def _render_visuals(frame: pd.DataFrame, chart_specs: list[dict[str, Any]]) -> None:
    st.subheader("Patterns and relationships")
    if frame.empty:
        st.info("No records match the active filters.")
        return
    if not chart_specs:
        st.info("This dataset does not contain enough compatible fields for dashboard charts.")
        return
    for index in range(0, len(chart_specs), 2):
        columns = st.columns(2)
        for container, spec in zip(columns, chart_specs[index : index + 2]):
            with container:
                _render_chart(frame, spec)


def _render_findings(state: dict[str, Any]) -> None:
    st.subheader("Findings and recommendations")
    insights = state.get("insights", [])
    if not insights:
        st.info("No findings were generated for this run.")
        return
    for insight in insights:
        label = insight.get("type", "finding").replace("_", " ").title()
        st.markdown(f"**{label}:** {insight.get('text', '')}")


def _render_data_explorer(frame: pd.DataFrame, state: dict[str, Any]) -> None:
    st.subheader("Cleaned data explorer")
    if frame.empty:
        st.info("No records match the active filters.")
        return
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name=f"{state['request'].run_id}-filtered.csv",
        mime="text/csv",
    )
    with st.expander("Transformation log"):
        transformations = state.get("transformations", [])
        if transformations:
            st.json(transformations)
        else:
            st.write("No cleaning transformations were required.")


def render_dashboard(state: dict[str, Any]) -> None:
    """Render a summary-first interactive dashboard for one completed run."""

    frame = state_frame(state)
    metadata = state.get("dataframe_metadata", {})
    date_column, category_column = filter_candidates(frame, metadata)
    with st.sidebar:
        st.header("Dashboard filters")
        date_range: tuple[object, object] | None = None
        category_values: list[object] | None = None
        if date_column:
            dates = pd.to_datetime(frame[date_column], errors="coerce", format="mixed").dropna()
            if not dates.empty:
                date_range = tuple(st.date_input("Date range", value=(dates.min().date(), dates.max().date())))
        if category_column:
            options = sorted(frame[category_column].dropna().unique().tolist())
            category_values = st.multiselect("Segment", options, default=options)
        if not date_column and not category_column:
            st.caption("No global filters are available for this dataset.")

    filtered = apply_filters(frame, date_column, date_range, category_column, category_values)
    _render_kpis(filtered, state.get("profile", {}))
    _render_visuals(filtered, state.get("chart_specs", []))
    st.caption("Filters update the metrics, charts, and data explorer. Findings summarize the full completed run.")
    _render_findings(state)
    _render_data_explorer(filtered, state)
