"""Streamlit entry point for the AutoInsights prototype."""

from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

import streamlit as st


# Allow `streamlit run frontend/streamlit_app.py` from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import MAX_UPLOAD_MB
from app.graph import run_analysis
from app.schemas import AnalysisRequest, RunStatus, SourceType


st.set_page_config(page_title="AutoInsights", page_icon="📊", layout="wide")


def _start_run(
    problem_statement: str,
    domain: str,
    constraints: str,
    uploaded_file: object | None,
    use_sample_data: bool,
) -> None:
    """Validate the form and retain the final graph state in the session."""

    if len(problem_statement.strip()) < 3:
        st.error("Enter a question with at least three characters.")
        return
    if not use_sample_data and uploaded_file is None:
        st.error("Upload a CSV file or select the included sample data.")
        return

    source_type = SourceType.SAMPLE if use_sample_data else SourceType.UPLOAD
    request = AnalysisRequest(
        run_id=f"run-{uuid4().hex[:12]}",
        problem_statement=problem_statement,
        domain=domain or None,
        constraints=constraints or None,
        source_type=source_type,
    )

    with st.status("Running AutoInsights workflow...", expanded=True) as status:
        state = run_analysis(request, uploaded_file=uploaded_file)  # type: ignore[arg-type]
        for event in state["progress"]:
            if event["level"] == "error":
                st.error(f"{event['agent']}: {event['message']}")
            elif event["level"] == "warning":
                st.warning(f"{event['agent']}: {event['message']}")
            else:
                st.write(f"{event['agent']}: {event['message']}")
        if state["status"] is RunStatus.COMPLETED:
            status.update(label="Analysis workflow complete", state="complete")
        else:
            status.update(label="Analysis workflow stopped", state="error")

    st.session_state.analysis_state = state


def _show_run_summary() -> None:
    """Display the result handoff until the full dashboard is added in Step 7."""

    state = st.session_state.get("analysis_state")
    if not state:
        st.info("Submit a question and data source to start an analysis run.")
        return
    if state["status"] is RunStatus.FAILED:
        st.error("The analysis could not be completed.")
        for error in state["errors"]:
            st.write(f"- {error}")
        return

    profile = state.get("profile", {})
    st.success(f"Run `{state['request'].run_id}` completed.")
    first, second, third = st.columns(3)
    first.metric("Rows analyzed", profile.get("row_count", "-"))
    second.metric("Columns", profile.get("column_count", "-"))
    third.metric("Charts prepared", len(state.get("chart_specs", [])))

    if state["warnings"]:
        st.subheader("Data-quality warnings")
        for warning in state["warnings"]:
            st.warning(warning)

    st.subheader("Workflow handoff")
    st.write(
        "The analysis state is ready. Step 7 will render the prepared charts, "
        "data explorer, findings, and downloads as the interactive dashboard."
    )


st.title("AutoInsights")
st.caption("Agentic data analysis prototype powered by Streamlit and LangGraph")

with st.form("analysis_request", clear_on_submit=False):
    problem_statement = st.text_area(
        "What would you like to learn from your data?",
        placeholder="Example: Identify the factors associated with monthly sales.",
    )
    left, right = st.columns(2)
    domain = left.text_input("Domain (optional)", placeholder="Example: retail")
    constraints = right.text_input("Constraints (optional)", placeholder="Example: focus on revenue")
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
        help=f"Maximum upload size: {MAX_UPLOAD_MB} MB.",
    )
    use_sample_data = st.checkbox("Use the included retail sales sample data instead")
    submitted = st.form_submit_button("Start analysis", type="primary")

if submitted:
    _start_run(problem_statement, domain, constraints, uploaded_file, use_sample_data)

_show_run_summary()
