"""Report agents that persist raw and cleaned analysis artifacts."""

from __future__ import annotations

from app.schemas import AnalysisState, ProgressEvent, RunStatus
from app.services.reporting import persist_and_render_report


def _progress(state: AnalysisState, message: str) -> list[ProgressEvent]:
    return [*state["progress"], {"agent": "Reporting Agent", "message": message, "level": "info"}]


def assessment_report_agent(state: AnalysisState) -> dict[str, object]:
    path = persist_and_render_report(state, "assessment")
    return {
        "assessment_report_path": path,
        "input_path": state["artifacts"].input_csv,
        "progress": _progress(state, "Saved the raw-data assessment report."),
    }


def final_report_agent(state: AnalysisState) -> dict[str, object]:
    path = persist_and_render_report(state, "final")
    return {
        "report_path": path,
        "input_path": state["artifacts"].input_csv,
        "cleaned_path": state["artifacts"].cleaned_csv,
        "status": RunStatus.COMPLETED,
        "progress": _progress(state, "Saved the cleaned-data descriptive report."),
    }
