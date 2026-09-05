"""LangGraph skeleton for the AutoInsights analysis workflow.

This module coordinates the raw-data assessment and approved-cleaning phases.
"""

from __future__ import annotations

from typing import BinaryIO, Literal, cast

from langgraph.graph import END, START, StateGraph

from app.agents import (
    cleaning_agent,
    cleaning_plan_agent,
    eda_agent,
    feature_engineering_agent,
    intake_agent,
    insight_agent,
    profiling_agent,
    sample_acquisition_agent,
    statistics_agent,
    upload_source_agent,
    visualization_agent,
)
from app.agents.reporting import assessment_report_agent, final_report_agent
from app.config import ARTIFACTS_DIR, MAX_UPLOAD_BYTES
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


def route_source(state: AnalysisState) -> Literal["upload_source", "sample_acquisition"]:
    """Choose the workflow branch from the validated request source type."""

    if state["request"].source_type is SourceType.UPLOAD:
        return "upload_source"
    return "sample_acquisition"


def route_after_intake(state: AnalysisState) -> Literal["upload_source", "sample_acquisition", "failure_handoff"]:
    """Stop immediately when intake determines a run cannot proceed."""

    if state["status"] is RunStatus.FAILED:
        return "failure_handoff"
    return route_source(state)


def route_after_source(state: AnalysisState) -> Literal["profiling", "failure_handoff"]:
    """Do not profile if source parsing or acquisition failed."""

    return "failure_handoff" if state["status"] is RunStatus.FAILED else "profiling"


def failure_handoff_agent(state: AnalysisState) -> dict[str, object]:
    """Terminal path that retains a friendly error state for Streamlit."""

    return _progress_update(
        state,
        agent="Workflow Manager",
        message="Analysis stopped because the input could not be processed.",
        level="error",
    )


def _add_analysis_nodes(graph: StateGraph) -> None:
    """Add agents shared by the assessment and post-cleaning workflows."""

    graph.add_node("profiling", profiling_agent)
    graph.add_node("eda", eda_agent)
    graph.add_node("feature_engineering", feature_engineering_agent)
    graph.add_node("statistics", statistics_agent)
    graph.add_node("insights", insight_agent)
    graph.add_node("visualization", visualization_agent)


def _add_post_profile_edges(graph: StateGraph, end_node: str) -> None:
    graph.add_edge("profiling", "eda")
    graph.add_edge("eda", "feature_engineering")
    graph.add_edge("feature_engineering", "statistics")
    graph.add_edge("statistics", "insights")
    graph.add_edge("insights", "visualization")
    graph.add_edge("visualization", end_node)


def build_assessment_graph():
    """Compile the raw-data assessment graph that pauses before cleaning."""

    graph = StateGraph(AnalysisState)
    graph.add_node("intake", intake_agent)
    graph.add_node("upload_source", upload_source_agent)
    graph.add_node("sample_acquisition", sample_acquisition_agent)
    graph.add_node("cleaning_plan", cleaning_plan_agent)
    graph.add_node("assessment_report", assessment_report_agent)
    graph.add_node("failure_handoff", failure_handoff_agent)
    _add_analysis_nodes(graph)

    graph.add_edge(START, "intake")
    graph.add_conditional_edges("intake", route_after_intake)
    graph.add_conditional_edges("upload_source", route_after_source)
    graph.add_conditional_edges("sample_acquisition", route_after_source)
    _add_post_profile_edges(graph, "cleaning_plan")
    graph.add_edge("cleaning_plan", "assessment_report")
    graph.add_edge("assessment_report", END)
    graph.add_edge("failure_handoff", END)

    return graph.compile()


def build_cleaning_graph():
    """Compile the approved-cleaning graph that regenerates final results."""

    graph = StateGraph(AnalysisState)
    graph.add_node("cleaning", cleaning_agent)
    graph.add_node("reporting_handoff", final_report_agent)
    _add_analysis_nodes(graph)
    graph.add_edge(START, "cleaning")
    graph.add_edge("cleaning", "profiling")
    _add_post_profile_edges(graph, "reporting_handoff")
    graph.add_edge("reporting_handoff", END)
    return graph.compile()


def build_analysis_graph():
    """Backward-compatible name for the initial assessment graph."""

    return build_assessment_graph()


_ASSESSMENT_GRAPH = build_assessment_graph()
_CLEANING_GRAPH = build_cleaning_graph()


def run_analysis(
    request: AnalysisRequest,
    uploaded_file: BinaryIO | None = None,
) -> AnalysisState:
    """Assess raw data and pause at the user-approval cleaning gate.

    The uploaded file is read into JSON-compatible graph state. The assessment
    phase persists the original source and pauses before transformations run.
    """

    source_csv: str | None = None
    if request.source_type is SourceType.UPLOAD and uploaded_file is not None:
        contents = uploaded_file.read(MAX_UPLOAD_BYTES + 1)
        if len(contents) <= MAX_UPLOAD_BYTES:
            try:
                source_csv = contents.decode("utf-8-sig")
            except UnicodeDecodeError:
                source_csv = None
    initial_state: AnalysisState = {
        "request": request,
        "artifacts": build_artifact_paths(ARTIFACTS_DIR, request.run_id),
        "status": RunStatus.RUNNING,
        "input_path": None,
        "cleaned_path": None,
        "source_csv": source_csv,
        "data_records": [],
        "progress": [],
        "warnings": [],
        "errors": [],
    }
    return cast(AnalysisState, _ASSESSMENT_GRAPH.invoke(initial_state))


def execute_cleaning(state: AnalysisState) -> AnalysisState:
    """Execute the approved cleaning plan and regenerate final analysis results."""

    if state["status"] is not RunStatus.AWAITING_CLEANING_APPROVAL:
        raise ValueError("Cleaning can only run after an assessment is awaiting approval.")
    return cast(AnalysisState, _CLEANING_GRAPH.invoke(state))
