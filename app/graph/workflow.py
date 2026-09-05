"""LangGraph skeleton for the AutoInsights analysis workflow.

This module establishes the graph shape and shared entry point. Agent nodes are
intentionally placeholders until the core and analytical implementations land.
"""

from __future__ import annotations

from typing import BinaryIO, Literal, cast

from langgraph.graph import END, START, StateGraph

from app.config import ARTIFACTS_DIR
from app.schemas import (
    AnalysisRequest,
    AnalysisState,
    ProgressEvent,
    RunStatus,
    SourceType,
)
from app.services import build_artifact_paths


def _progress_update(
    state: AnalysisState,
    *,
    agent: str,
    message: str,
    level: Literal["info", "warning", "error"] = "info",
) -> dict[str, object]:
    """Return a state update that preserves prior progress messages."""

    event: ProgressEvent = {"agent": agent, "message": message, "level": level}
    return {"progress": [*state["progress"], event]}


def intake_agent(state: AnalysisState) -> dict[str, object]:
    """Placeholder for request and CSV validation in Step 4."""

    return _progress_update(
        state,
        agent="Intake Agent",
        message="Request accepted; validation will be implemented in Step 4.",
    )


def upload_source_agent(state: AnalysisState) -> dict[str, object]:
    """Placeholder for processing an uploaded file in Step 4."""

    return _progress_update(
        state,
        agent="Uploaded Data Source",
        message="Uploaded-data path selected; CSV persistence will be implemented in Step 4.",
    )


def sample_acquisition_agent(state: AnalysisState) -> dict[str, object]:
    """Placeholder for selecting the bundled sample dataset in Step 4."""

    return _progress_update(
        state,
        agent="Data Acquisition Agent",
        message="Sample-data path selected; acquisition will be implemented in Step 4.",
    )


def profiling_agent(state: AnalysisState) -> dict[str, object]:
    return _progress_update(
        state,
        agent="Data Profiling Agent",
        message="Profiling placeholder completed.",
    )


def cleaning_agent(state: AnalysisState) -> dict[str, object]:
    return _progress_update(
        state,
        agent="Data Cleaning Agent",
        message="Cleaning placeholder completed.",
    )


def eda_agent(state: AnalysisState) -> dict[str, object]:
    return _progress_update(
        state,
        agent="EDA Agent",
        message="Exploratory analysis placeholder completed.",
    )


def feature_engineering_agent(state: AnalysisState) -> dict[str, object]:
    return _progress_update(
        state,
        agent="Feature Engineering Agent",
        message="Feature preparation placeholder completed.",
    )


def statistics_agent(state: AnalysisState) -> dict[str, object]:
    return _progress_update(
        state,
        agent="Statistical Analysis Agent",
        message="Statistical analysis placeholder completed.",
    )


def insight_agent(state: AnalysisState) -> dict[str, object]:
    return _progress_update(
        state,
        agent="Insight Generation Agent",
        message="Insight generation placeholder completed.",
    )


def visualization_agent(state: AnalysisState) -> dict[str, object]:
    return _progress_update(
        state,
        agent="Visualization Agent",
        message="Visualization metadata placeholder completed.",
    )


def reporting_handoff_agent(state: AnalysisState) -> dict[str, object]:
    """Finish the skeleton run; report generation is implemented in Step 8."""

    update = _progress_update(
        state,
        agent="Reporting Handoff",
        message="Workflow skeleton completed; reporting will be implemented in Step 8.",
    )
    update["status"] = RunStatus.COMPLETED
    return update


def route_source(state: AnalysisState) -> Literal["upload_source", "sample_acquisition"]:
    """Choose the workflow branch from the validated request source type."""

    if state["request"].source_type is SourceType.UPLOAD:
        return "upload_source"
    return "sample_acquisition"


def build_analysis_graph():
    """Compile the workflow graph used by the prototype."""

    graph = StateGraph(AnalysisState)
    graph.add_node("intake", intake_agent)
    graph.add_node("upload_source", upload_source_agent)
    graph.add_node("sample_acquisition", sample_acquisition_agent)
    graph.add_node("profiling", profiling_agent)
    graph.add_node("cleaning", cleaning_agent)
    graph.add_node("eda", eda_agent)
    graph.add_node("feature_engineering", feature_engineering_agent)
    graph.add_node("statistics", statistics_agent)
    graph.add_node("insights", insight_agent)
    graph.add_node("visualization", visualization_agent)
    graph.add_node("reporting_handoff", reporting_handoff_agent)

    graph.add_edge(START, "intake")
    graph.add_conditional_edges("intake", route_source)
    graph.add_edge("upload_source", "profiling")
    graph.add_edge("sample_acquisition", "profiling")
    graph.add_edge("profiling", "cleaning")
    graph.add_edge("cleaning", "eda")
    graph.add_edge("eda", "feature_engineering")
    graph.add_edge("feature_engineering", "statistics")
    graph.add_edge("statistics", "insights")
    graph.add_edge("insights", "visualization")
    graph.add_edge("visualization", "reporting_handoff")
    graph.add_edge("reporting_handoff", END)

    return graph.compile()


_COMPILED_GRAPH = build_analysis_graph()


def run_analysis(
    request: AnalysisRequest,
    uploaded_file: BinaryIO | None = None,
) -> AnalysisState:
    """Run the current workflow skeleton.

    `uploaded_file` is reserved for Step 4, when the intake and acquisition
    agents will save and validate input data. Keeping it here now fixes the UI
    integration contract before the agent implementations are added.
    """

    _ = uploaded_file
    initial_state: AnalysisState = {
        "request": request,
        "artifacts": build_artifact_paths(ARTIFACTS_DIR, request.run_id),
        "status": RunStatus.RUNNING,
        "input_path": None,
        "cleaned_path": None,
        "progress": [],
        "warnings": [],
        "errors": [],
    }
    return cast(AnalysisState, _COMPILED_GRAPH.invoke(initial_state))
