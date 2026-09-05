"""Pure dashboard filter helpers shared by the UI and tests."""

from __future__ import annotations

from typing import Any

import pandas as pd


def filter_candidates(frame: pd.DataFrame, metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    """Choose an optional date and categorical filter from agent metadata."""

    date_column = next((column for column in metadata.get("date_columns", []) if column in frame), None)
    category_column = next(
        (
            column
            for column in metadata.get("categorical_columns", [])
            if column in frame and column != date_column and 2 <= frame[column].nunique(dropna=True) <= 12
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
    """Return a copy filtered by inclusive date and categorical selections."""

    filtered = frame.copy()
    if date_column and date_range and date_column in filtered:
        dates = pd.to_datetime(filtered[date_column], errors="coerce", format="mixed")
        filtered = filtered.loc[dates.between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]), inclusive="both")].copy()
    if category_column and category_values and category_column in filtered:
        filtered = filtered[filtered[category_column].isin(category_values)].copy()
    return filtered
