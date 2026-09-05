"""Core deterministic agents for CSV intake, profiling, and cleaning."""

from __future__ import annotations

from io import StringIO
import json
import re
from typing import Any

import pandas as pd

from app.config import PROJECT_ROOT
from app.schemas import AnalysisState, ProgressEvent, RunStatus


SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "sample" / "retail_sales_demo.csv"


def _event(agent: str, message: str, level: str = "info") -> ProgressEvent:
    return {"agent": agent, "message": message, "level": level}  # type: ignore[typeddict-item]


def _progress(state: AnalysisState, event: ProgressEvent) -> list[ProgressEvent]:
    return [*state["progress"], event]


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Produce JSON-safe records that remain valid graph state."""

    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _frame_from_state(state: AnalysisState) -> pd.DataFrame:
    return pd.DataFrame(state["data_records"])


def _fail(state: AnalysisState, agent: str, message: str) -> dict[str, object]:
    return {
        "status": RunStatus.FAILED,
        "errors": [*state["errors"], message],
        "progress": _progress(state, _event(agent, message, "error")),
    }


def intake_agent(state: AnalysisState) -> dict[str, object]:
    """Validate the request and that an uploaded source was supplied."""

    request = state["request"]
    if request.source_type.value == "upload" and not state["source_csv"]:
        return _fail(state, "Intake Agent", "Please upload a non-empty CSV file.")

    return {
        "progress": _progress(
            state,
            _event("Intake Agent", "Request validated. Preparing the selected data source."),
        )
    }


def upload_source_agent(state: AnalysisState) -> dict[str, object]:
    """Parse an uploaded CSV source into graph-safe records."""

    try:
        frame = pd.read_csv(StringIO(state["source_csv"] or ""))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeError) as error:
        return _fail(state, "Uploaded Data Source", f"The uploaded file is not a readable CSV: {error}")

    if frame.empty or not len(frame.columns):
        return _fail(state, "Uploaded Data Source", "The uploaded CSV has no data rows or columns.")

    return {
        "data_records": _records(frame),
        "dataframe_metadata": {"source": "upload", "original_columns": list(frame.columns)},
        "progress": _progress(
            state,
            _event("Uploaded Data Source", f"Loaded {len(frame):,} rows and {len(frame.columns)} columns."),
        ),
    }


def sample_acquisition_agent(state: AnalysisState) -> dict[str, object]:
    """Load the project-owned synthetic sample dataset."""

    try:
        frame = pd.read_csv(SAMPLE_DATA_PATH)
    except (OSError, pd.errors.ParserError) as error:
        return _fail(state, "Data Acquisition Agent", f"The bundled sample data could not be loaded: {error}")

    return {
        "source_csv": SAMPLE_DATA_PATH.read_text(encoding="utf-8"),
        "data_records": _records(frame),
        "dataframe_metadata": {
            "source": "sample",
            "source_name": "Retail Sales Demo Data",
            "original_columns": list(frame.columns),
        },
        "progress": _progress(
            state,
            _event("Data Acquisition Agent", f"Loaded the sample dataset with {len(frame):,} rows."),
        ),
    }


def profiling_agent(state: AnalysisState) -> dict[str, object]:
    """Summarize schema and data-quality signals without modifying data."""

    frame = _frame_from_state(state)
    if frame.empty:
        return _fail(state, "Data Profiling Agent", "No records are available to profile.")

    null_percent = (frame.isna().mean() * 100).round(2).to_dict()
    duplicate_count = int(frame.duplicated().sum())
    numeric = frame.select_dtypes(include="number")
    numeric_summary = numeric.describe().round(3).to_dict() if not numeric.empty else {}
    warnings: list[str] = []
    for column, percentage in null_percent.items():
        if percentage > 0:
            warnings.append(f"{column} has {percentage}% missing values.")
    if duplicate_count:
        warnings.append(f"{duplicate_count} duplicate row(s) detected.")

    profile = {
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": [
            {"name": column, "dtype": str(dtype), "null_percent": null_percent[column]}
            for column, dtype in frame.dtypes.items()
        ],
        "duplicate_rows": duplicate_count,
        "numeric_summary": numeric_summary,
    }
    metadata = {**state.get("dataframe_metadata", {}), "row_count": len(frame), "column_count": len(frame.columns)}
    return {
        "profile": profile,
        "dataframe_metadata": metadata,
        "warnings": warnings,
        "progress": _progress(
            state,
            _event("Data Profiling Agent", "Profiled schema, missing values, duplicates, and numeric summaries."),
        ),
    }


def _normalized_columns(columns: pd.Index) -> list[str]:
    result: list[str] = []
    used: set[str] = set()
    for index, column in enumerate(columns, start=1):
        base = re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_") or f"column_{index}"
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        result.append(candidate)
    return result


def cleaning_agent(state: AnalysisState) -> dict[str, object]:
    """Apply transparent, low-risk cleaning and log every transformation."""

    frame = _frame_from_state(state).copy()
    if frame.empty:
        return _fail(state, "Data Cleaning Agent", "No records are available to clean.")

    transformations: list[dict[str, Any]] = []
    old_columns = list(frame.columns)
    new_columns = _normalized_columns(frame.columns)
    if old_columns != new_columns:
        frame.columns = new_columns
        transformations.append({"action": "normalize_column_names", "before": old_columns, "after": new_columns})

    object_columns = frame.select_dtypes(include="object").columns
    for column in object_columns:
        original = frame[column].copy()
        frame[column] = frame[column].str.strip().replace("", pd.NA)
        changed = int((original.fillna("<NA>") != frame[column].fillna("<NA>")).sum())
        if changed:
            transformations.append({"action": "trim_text_values", "column": column, "rows_affected": changed})

    duplicate_count = int(frame.duplicated().sum())
    if duplicate_count:
        frame = frame.drop_duplicates().reset_index(drop=True)
        transformations.append({"action": "remove_duplicates", "rows_affected": duplicate_count})

    for column in frame.columns:
        missing_count = int(frame[column].isna().sum())
        if not missing_count:
            continue
        if pd.api.types.is_numeric_dtype(frame[column]):
            value = frame[column].median()
            if pd.notna(value):
                frame[column] = frame[column].fillna(value)
                transformations.append(
                    {"action": "impute_numeric_median", "column": column, "rows_affected": missing_count}
                )
        elif frame[column].dropna().size:
            value = frame[column].mode(dropna=True).iloc[0]
            frame[column] = frame[column].fillna(value)
            transformations.append(
                {"action": "impute_categorical_mode", "column": column, "rows_affected": missing_count}
            )

    return {
        "data_records": _records(frame),
        "transformations": transformations,
        "dataframe_metadata": {
            **state.get("dataframe_metadata", {}),
            "cleaned_row_count": len(frame),
            "cleaned_columns": list(frame.columns),
        },
        "progress": _progress(
            state,
            _event("Data Cleaning Agent", f"Completed {len(transformations)} deterministic transformation(s)."),
        ),
    }


def cleaning_plan_agent(state: AnalysisState) -> dict[str, object]:
    """Describe intended cleaning actions without modifying the dataset."""

    frame = _frame_from_state(state)
    preview = frame.copy()
    plan: list[dict[str, Any]] = []
    normalized = _normalized_columns(frame.columns)
    if list(frame.columns) != normalized:
        plan.append({"action": "normalize_column_names", "details": "Convert column names to snake_case."})
        preview.columns = normalized

    text_columns = frame.select_dtypes(include="object").columns.tolist()
    whitespace_cells = sum(
        int((frame[column].dropna().astype(str) != frame[column].dropna().astype(str).str.strip()).sum())
        for column in text_columns
    )
    if whitespace_cells:
        plan.append({"action": "trim_text_values", "rows_affected": whitespace_cells, "details": "Trim leading and trailing whitespace."})
    for column in preview.select_dtypes(include="object").columns:
        preview[column] = preview[column].str.strip().replace("", pd.NA)

    duplicate_count = int(preview.duplicated().sum())
    if duplicate_count:
        plan.append({"action": "remove_duplicates", "rows_affected": duplicate_count, "details": "Remove exact duplicate rows."})

    for column in preview.columns:
        missing_count = int(preview[column].isna().sum())
        if not missing_count:
            continue
        strategy = "impute_numeric_median" if pd.api.types.is_numeric_dtype(preview[column]) else "impute_categorical_mode"
        plan.append(
            {
                "action": strategy,
                "column": column,
                "rows_affected": missing_count,
                "details": "Fill missing values using the median." if strategy == "impute_numeric_median" else "Fill missing values using the most frequent value.",
            }
        )

    if not plan:
        plan.append({"action": "no_changes", "details": "No deterministic cleaning actions are currently required."})

    return {
        "cleaning_plan": plan,
        "status": RunStatus.AWAITING_CLEANING_APPROVAL,
        "progress": _progress(
            state,
            _event("Data Cleaning Agent", "Prepared a cleaning plan and is awaiting user approval."),
        ),
    }
