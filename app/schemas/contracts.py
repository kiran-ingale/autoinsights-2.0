"""Shared types exchanged between the UI, workflow agents, and report service."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal, NotRequired, TypedDict

from pydantic import BaseModel, Field, field_validator


class SourceType(StrEnum):
    """Where a run's input data originates."""

    UPLOAD = "upload"
    SAMPLE = "sample"


class RunStatus(StrEnum):
    """Lifecycle states displayed by the Streamlit interface."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRequest(BaseModel):
    """Validated user input used to start one analysis run."""

    run_id: str = Field(min_length=1, description="Unique identifier for one run.")
    problem_statement: str = Field(
        min_length=3,
        max_length=2_000,
        description="Question the analysis should answer.",
    )
    domain: str | None = Field(default=None, max_length=200)
    constraints: str | None = Field(default=None, max_length=1_000)
    source_type: SourceType

    @field_validator("problem_statement", "domain", "constraints", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ArtifactPaths(BaseModel):
    """Canonical locations for the outputs of a single analysis run."""

    root_dir: str
    input_csv: str
    cleaned_csv: str
    transformations_json: str
    charts_dir: str
    report_html: str
    metadata_json: str


class ProgressEvent(TypedDict):
    """A user-safe workflow update for the Streamlit progress display."""

    agent: str
    message: str
    level: Literal["info", "warning", "error"]


class AnalysisState(TypedDict):
    """LangGraph state contract.

    Fields are intentionally JSON-compatible so the state can be displayed,
    serialized to artifacts, and later moved to a background worker if needed.
    """

    request: AnalysisRequest
    artifacts: ArtifactPaths
    status: RunStatus
    input_path: str | None
    cleaned_path: str | None
    source_csv: str | None
    data_records: list[dict[str, Any]]
    progress: list[ProgressEvent]
    warnings: list[str]
    errors: list[str]

    dataframe_metadata: NotRequired[dict[str, Any]]
    profile: NotRequired[dict[str, Any]]
    transformations: NotRequired[list[dict[str, Any]]]
    observations: NotRequired[list[str]]
    statistics: NotRequired[dict[str, Any]]
    insights: NotRequired[list[dict[str, str]]]
    chart_specs: NotRequired[list[dict[str, Any]]]
    report_path: NotRequired[str]
