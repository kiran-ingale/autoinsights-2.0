"""Deterministic analytical agents that prepare dashboard-ready results."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from app.schemas import AnalysisState, ProgressEvent


def _event(agent: str, message: str) -> ProgressEvent:
    return {"agent": agent, "message": message, "level": "info"}


def _progress(state: AnalysisState, event: ProgressEvent) -> list[ProgressEvent]:
    return [*state["progress"], event]


def _frame(state: AnalysisState) -> pd.DataFrame:
    return pd.DataFrame(state["data_records"])


def _json_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _date_columns(frame: pd.DataFrame) -> list[str]:
    """Identify string columns that are substantially parseable as dates."""

    candidates: list[str] = []
    for column in frame.columns:
        if not (pd.api.types.is_object_dtype(frame[column]) or "date" in column.lower()):
            continue
        parsed = pd.to_datetime(frame[column], errors="coerce", format="mixed")
        if parsed.notna().mean() >= 0.8:
            candidates.append(column)
    return candidates


def eda_agent(state: AnalysisState) -> dict[str, object]:
    """Find compact, evidence-based observations and chart candidates."""

    frame = _frame(state)
    numeric_columns = list(frame.select_dtypes(include="number").columns)
    categorical_columns = list(frame.select_dtypes(exclude="number").columns)
    date_columns = _date_columns(frame)
    observations: list[str] = []

    if numeric_columns:
        for column in numeric_columns[:3]:
            series = frame[column]
            observations.append(
                f"{column} ranges from {series.min():.2f} to {series.max():.2f}, with a mean of {series.mean():.2f}."
            )
    for column in categorical_columns[:2]:
        counts = frame[column].value_counts(dropna=False)
        if 1 < len(counts) <= 12:
            observations.append(
                f"{column} contains {len(counts)} distinct value(s); {counts.index[0]} is the most frequent."
            )
    if date_columns:
        observations.append(f"{date_columns[0]} is suitable for time-based analysis.")

    return {
        "observations": observations,
        "dataframe_metadata": {
            **state.get("dataframe_metadata", {}),
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "date_columns": date_columns,
        },
        "progress": _progress(
            state,
            _event("EDA Agent", f"Generated exploratory observations from {len(frame):,} cleaned record(s)."),
        ),
    }


def feature_engineering_agent(state: AnalysisState) -> dict[str, object]:
    """Describe safe, potential model features without mutating cleaned data."""

    metadata = state.get("dataframe_metadata", {})
    numeric_columns = metadata.get("numeric_columns", [])
    categorical_columns = metadata.get("categorical_columns", [])
    date_columns = metadata.get("date_columns", [])
    recommendations: list[dict[str, str]] = []

    for column in categorical_columns:
        recommendations.append({"column": column, "recommended_transform": "one_hot_encode"})
    for column in numeric_columns:
        recommendations.append({"column": column, "recommended_transform": "standard_scale_if_modeling"})
    for column in date_columns:
        recommendations.append({"column": column, "recommended_transform": "derive_year_month_weekday"})

    return {
        "dataframe_metadata": {
            **metadata,
            "feature_recommendations": recommendations,
        },
        "progress": _progress(
            state,
            _event("Feature Engineering Agent", "Identified model-ready feature transformations without altering cleaned data."),
        ),
    }


def statistics_agent(state: AnalysisState) -> dict[str, object]:
    """Calculate descriptive statistics and Pearson correlations when supported."""

    frame = _frame(state)
    numeric = frame.select_dtypes(include="number")
    correlations: dict[str, dict[str, float]] = {}
    strongest_pair: dict[str, Any] | None = None
    if len(numeric.columns) >= 2:
        correlation_frame = numeric.corr().round(4)
        correlations = correlation_frame.to_dict()
        pairs: list[tuple[str, str, float]] = []
        for index, left in enumerate(correlation_frame.columns):
            for right in correlation_frame.columns[index + 1 :]:
                value = correlation_frame.loc[left, right]
                if pd.notna(value):
                    pairs.append((left, right, float(value)))
        if pairs:
            left, right, value = max(pairs, key=lambda item: abs(item[2]))
            strongest_pair = {"x": left, "y": right, "pearson_r": value, "sample_size": len(frame)}

    statistics = {
        "numeric_column_count": len(numeric.columns),
        "correlations": correlations,
        "strongest_correlation": strongest_pair,
    }
    return {
        "statistics": statistics,
        "progress": _progress(
            state,
            _event("Statistical Analysis Agent", "Calculated descriptive associations; correlations are non-causal."),
        ),
    }


def insight_agent(state: AnalysisState) -> dict[str, object]:
    """Translate measured results into bounded findings and recommendations."""

    profile = state.get("profile", {})
    statistics = state.get("statistics", {})
    insights: list[dict[str, str]] = []
    strongest = statistics.get("strongest_correlation")

    if strongest:
        direction = "positive" if strongest["pearson_r"] >= 0 else "negative"
        insights.append(
            {
                "type": "finding",
                "text": (
                    f"{strongest['x']} and {strongest['y']} have the strongest observed "
                    f"{direction} Pearson correlation (r={strongest['pearson_r']:.2f}, n={strongest['sample_size']})."
                ),
            }
        )
        insights.append(
            {
                "type": "recommendation",
                "text": "Investigate this relationship by segment before using it for a business decision; correlation does not establish causation.",
            }
        )
    else:
        insights.append(
            {
                "type": "recommendation",
                "text": "Collect at least two comparable numeric measures to support relationship analysis.",
            }
        )

    if profile.get("duplicate_rows", 0):
        insights.append(
            {
                "type": "data_quality",
                "text": "Duplicate rows were detected in the source; use the cleaned data for subsequent analysis.",
            }
        )
    insights.append(
        {
            "type": "limitation",
            "text": "Results describe the provided dataset only and should be reviewed with domain context before action.",
        }
    )
    return {
        "insights": insights,
        "progress": _progress(
            state,
            _event("Insight Generation Agent", "Created evidence-linked findings, recommendations, and limitations."),
        ),
    }


def visualization_agent(state: AnalysisState) -> dict[str, object]:
    """Create compact serializable chart specifications for the Streamlit dashboard."""

    frame = _frame(state)
    metadata = state.get("dataframe_metadata", {})
    numeric_columns: list[str] = metadata.get("numeric_columns", [])
    categorical_columns: list[str] = metadata.get("categorical_columns", [])
    date_columns: list[str] = metadata.get("date_columns", [])
    specs: list[dict[str, Any]] = []

    for column in numeric_columns[:2]:
        specs.append(
            {
                "id": f"distribution_{column}",
                "type": "histogram",
                "title": f"Distribution of {column}",
                "x": column,
                "data": _json_records(frame[[column]]),
            }
        )

    if numeric_columns and categorical_columns:
        category = next((column for column in categorical_columns if 2 <= frame[column].nunique() <= 10), None)
        if category:
            measure = numeric_columns[0]
            grouped = frame.groupby(category, dropna=False)[measure].mean().sort_values(ascending=False).reset_index()
            specs.append(
                {
                    "id": f"comparison_{category}_{measure}",
                    "type": "bar",
                    "title": f"Average {measure} by {category}",
                    "x": category,
                    "y": measure,
                    "aggregation": "mean",
                    "data": _json_records(grouped),
                }
            )

    if len(numeric_columns) >= 2:
        correlation = frame[numeric_columns].corr().round(4)
        specs.append(
            {
                "id": "numeric_correlation",
                "type": "heatmap",
                "title": "Correlation among numeric measures",
                "x": list(correlation.columns),
                "y": list(correlation.index),
                "z": correlation.values.tolist(),
            }
        )
        if len(frame) >= 12:
            specs.append(
                {
                    "id": f"relationship_{numeric_columns[0]}_{numeric_columns[1]}",
                    "type": "scatter",
                    "title": f"{numeric_columns[0]} versus {numeric_columns[1]}",
                    "x": numeric_columns[0],
                    "y": numeric_columns[1],
                    "data": _json_records(frame[numeric_columns[:2]]),
                }
            )

    if date_columns and numeric_columns:
        date_column, measure = date_columns[0], numeric_columns[0]
        dated = frame[[date_column, measure]].copy()
        dated[date_column] = pd.to_datetime(dated[date_column], errors="coerce", format="mixed")
        dated = dated.dropna().sort_values(date_column)
        if dated[date_column].nunique() >= 8:
            specs.append(
                {
                    "id": f"trend_{date_column}_{measure}",
                    "type": "line",
                    "title": f"{measure} over {date_column}",
                    "x": date_column,
                    "y": measure,
                    "data": _json_records(dated),
                }
            )

    return {
        "chart_specs": specs,
        "progress": _progress(
            state,
            _event("Visualization Agent", f"Prepared {len(specs)} data-supported chart specification(s)."),
        ),
    }
